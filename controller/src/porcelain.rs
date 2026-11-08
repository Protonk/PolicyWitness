//! Closed binary primitives. Records are generated; semantic admission is separate.
#[cfg(test)]
use serde::Deserialize;
use serde::Serialize;
use std::cell::Cell;

pub fn charge(budget: &Cell<usize>, bytes: usize) -> Result<(), String> {
    budget.set(
        budget
            .get()
            .checked_sub(bytes)
            .ok_or("decoded storage budget")?,
    );
    Ok(())
}

pub const LIMIT: usize = 128 * 1024 * 1024;
const DEPTH: usize = 32;
pub trait WireRead: Sized {
    const KIND: u8;
    fn read_payload(data: &[u8], depth: usize, budget: &Cell<usize>) -> Result<Self, String>;
}

#[derive(Clone, Copy)]
pub struct WireValue<'a> {
    kind: u8,
    data: &'a [u8],
    depth: usize,
    budget: &'a Cell<usize>,
}
impl WireValue<'_> {
    pub fn decode<T: WireRead>(self) -> Result<T, String> {
        if self.kind != T::KIND {
            return Err("wrong scalar/record kind".into());
        }
        T::read_payload(self.data, self.depth, self.budget)
    }
    pub fn bytes(self) -> Result<Vec<u8>, String> {
        if self.kind != 5 {
            return Err("expected bytes".into());
        }
        charge(self.budget, self.data.len())?;
        let mut data = Vec::new();
        data.try_reserve_exact(self.data.len())
            .map_err(|_| "bytes allocation")?;
        data.extend_from_slice(self.data);
        Ok(data)
    }
}
struct Cursor<'a> {
    data: &'a [u8],
    offset: usize,
    depth: usize,
    budget: &'a Cell<usize>,
}
impl<'a> Cursor<'a> {
    fn new(data: &'a [u8], depth: usize, budget: &'a Cell<usize>) -> Result<Self, String> {
        if depth > DEPTH || data.len() > LIMIT {
            return Err("wire budget".into());
        }
        Ok(Self {
            data,
            offset: 0,
            depth,
            budget,
        })
    }
    fn take(&mut self, count: usize) -> Result<&'a [u8], String> {
        let end = self.offset.checked_add(count).ok_or("length overflow")?;
        let bytes = self.data.get(self.offset..end).ok_or("short wire value")?;
        self.offset = end;
        Ok(bytes)
    }
    fn u16(&mut self) -> Result<u16, String> {
        Ok(u16::from_le_bytes(self.take(2)?.try_into().unwrap()))
    }
    fn count(&mut self, minimum: usize) -> Result<usize, String> {
        let count = u32::from_le_bytes(self.take(4)?.try_into().unwrap()) as usize;
        if count > (self.data.len() - self.offset) / minimum {
            return Err("impossible collection count".into());
        }
        Ok(count)
    }
    fn value(&mut self) -> Result<WireValue<'a>, String> {
        let kind = self.take(1)?[0];
        if !(1..=9).contains(&kind) {
            return Err("unknown wire kind".into());
        }
        let len = u32::from_le_bytes(self.take(4)?.try_into().unwrap()) as usize;
        let data = self.take(len)?;
        if self.depth >= DEPTH {
            return Err("wire depth".into());
        }
        Ok(WireValue {
            kind,
            data,
            depth: self.depth + 1,
            budget: self.budget,
        })
    }
    fn finish(&self) -> Result<(), String> {
        if self.offset == self.data.len() {
            Ok(())
        } else {
            Err("trailing wire data".into())
        }
    }
}
pub struct RecordReader<'a> {
    cursor: Cursor<'a>,
    last: u16,
}
impl<'a> RecordReader<'a> {
    pub fn new(
        data: &'a [u8],
        id: u16,
        depth: usize,
        budget: &'a Cell<usize>,
    ) -> Result<Self, String> {
        let mut cursor = Cursor::new(data, depth, budget)?;
        if cursor.u16()? != id {
            return Err("wrong record identity".into());
        }
        Ok(Self { cursor, last: 0 })
    }
    pub fn next(&mut self) -> Result<Option<(u16, WireValue<'a>)>, String> {
        if self.cursor.offset == self.cursor.data.len() {
            return Ok(None);
        }
        let tag = self.cursor.u16()?;
        if tag <= self.last {
            return Err("duplicate or unordered field tag".into());
        }
        self.last = tag;
        Ok(Some((tag, self.cursor.value()?)))
    }
}
pub fn decode<T: WireRead>(data: &[u8]) -> Result<T, String> {
    if data.len() > LIMIT || data.get(..4) != Some(b"PWP1") {
        return Err("invalid porcelain frame".into());
    }
    if data.get(4..36) != Some(&crate::porcelain_records::FINGERPRINT) {
        return Err("unsupported porcelain schema".into());
    }
    let budget = Cell::new(LIMIT);
    let mut reader = Cursor::new(&data[36..], 0, &budget)?;
    let value = reader.value()?;
    reader.finish()?;
    value.decode()
}
pub fn variant<'a>(
    data: &'a [u8],
    depth: usize,
    budget: &'a Cell<usize>,
) -> Result<(u16, WireValue<'a>), String> {
    let mut reader = Cursor::new(data, depth, budget)?;
    let tag = reader.u16()?;
    let value = reader.value()?;
    reader.finish()?;
    Ok((tag, value))
}
impl WireRead for bool {
    const KIND: u8 = 1;
    fn read_payload(data: &[u8], _: usize, _budget: &Cell<usize>) -> Result<Self, String> {
        match data {
            [0] => Ok(false),
            [1] => Ok(true),
            _ => Err("invalid boolean".into()),
        }
    }
}
macro_rules! integer {
    ($t:ty,$wire:ty,$kind:expr) => {
        impl WireRead for $t {
            const KIND: u8 = $kind;
            fn read_payload(data: &[u8], _: usize, _budget: &Cell<usize>) -> Result<Self, String> {
                let bytes: [u8; 8] = data.try_into().map_err(|_| "integer width")?;
                Self::try_from(<$wire>::from_le_bytes(bytes)).map_err(|_| "integer range".into())
            }
        }
    };
}
integer!(i32, i64, 2);
integer!(i64, i64, 2);
integer!(u32, u64, 3);
integer!(u64, u64, 3);
impl WireRead for String {
    const KIND: u8 = 4;
    fn read_payload(data: &[u8], _: usize, _budget: &Cell<usize>) -> Result<Self, String> {
        let text = std::str::from_utf8(data).map_err(|_| "invalid UTF-8")?;
        charge(_budget, text.len())?;
        let mut result = String::new();
        result
            .try_reserve_exact(text.len())
            .map_err(|_| "text allocation")?;
        result.push_str(text);
        Ok(result)
    }
}
impl<T: WireRead> WireRead for Vec<T> {
    const KIND: u8 = 7;
    fn read_payload(data: &[u8], depth: usize, budget: &Cell<usize>) -> Result<Self, String> {
        let mut reader = Cursor::new(data, depth, budget)?;
        let count = reader.count(5)?;
        charge(
            budget,
            count
                .checked_mul(std::mem::size_of::<T>())
                .ok_or("list storage overflow")?,
        )?;
        let mut output = Vec::new();
        output
            .try_reserve_exact(count)
            .map_err(|_| "list allocation")?;
        for _ in 0..count {
            output.push(reader.value()?.decode()?);
        }
        reader.finish()?;
        Ok(output)
    }
}
/// Ordered unique entries have explicit contiguous storage and access. They are
/// not a general semantic tree; record fields remain statically named.
#[derive(Clone, Debug, PartialEq)]
pub struct OrderedMap<T>(pub Vec<(String, T)>);
impl<T: WireRead> WireRead for OrderedMap<T> {
    const KIND: u8 = 8;
    fn read_payload(data: &[u8], depth: usize, budget: &Cell<usize>) -> Result<Self, String> {
        let mut reader = Cursor::new(data, depth, budget)?;
        let count = reader.count(10)?;
        charge(
            budget,
            count
                .checked_mul(std::mem::size_of::<(String, T)>())
                .ok_or("map storage overflow")?,
        )?;
        let mut output: Vec<(String, T)> = Vec::new();
        output
            .try_reserve_exact(count)
            .map_err(|_| "map allocation")?;
        for _ in 0..count {
            let key: String = reader.value()?.decode()?;
            if output.last().is_some_and(|(last, _)| last >= &key) {
                return Err("duplicate or unordered map key".into());
            }
            output.push((key, reader.value()?.decode()?));
        }
        reader.finish()?;
        Ok(Self(output))
    }
}
impl<T: Serialize> Serialize for OrderedMap<T> {
    fn serialize<S: serde::Serializer>(&self, s: S) -> Result<S::Ok, S::Error> {
        use serde::ser::SerializeMap;
        let mut map = s.serialize_map(Some(self.0.len()))?;
        for (key, value) in &self.0 {
            map.serialize_entry(key, value)?;
        }
        map.end()
    }
}
// Authored fixture JSON enters through this test-comparison boundary; binary
// production reading above neither builds nor queries a string-keyed tree.
#[cfg(test)]
impl<'de, T: Deserialize<'de>> Deserialize<'de> for OrderedMap<T> {
    fn deserialize<D: serde::Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        struct Entries<T>(std::marker::PhantomData<T>);
        impl<'de, T: Deserialize<'de>> serde::de::Visitor<'de> for Entries<T> {
            type Value = OrderedMap<T>;
            fn expecting(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
                f.write_str("unique string-keyed entries")
            }
            fn visit_map<A: serde::de::MapAccess<'de>>(
                self,
                mut access: A,
            ) -> Result<Self::Value, A::Error> {
                let mut entries: Vec<(String, T)> = Vec::new();
                while let Some(entry) = access.next_entry()? {
                    entries.push(entry);
                }
                entries.sort_by(|a, b| a.0.cmp(&b.0));
                if entries.windows(2).any(|w| w[0].0 == w[1].0) {
                    return Err(serde::de::Error::custom("duplicate key"));
                }
                Ok(OrderedMap(entries))
            }
        }
        d.deserialize_map(Entries(std::marker::PhantomData))
    }
}
// Base64 exists exclusively at the public JSON byte projection and authored JSON
// fixture boundary. No internal field is converted through text for access.
pub struct Base64<'a>(pub &'a [u8]);
impl Serialize for Base64<'_> {
    fn serialize<S: serde::Serializer>(&self, s: S) -> Result<S::Ok, S::Error> {
        const ABC: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        let mut text = String::with_capacity(self.0.len().div_ceil(3) * 4);
        for bytes in self.0.chunks(3) {
            let a = bytes[0];
            let b = bytes.get(1).copied().unwrap_or(0);
            let c = bytes.get(2).copied().unwrap_or(0);
            text.push(ABC[(a >> 2) as usize] as char);
            text.push(ABC[((a & 3) << 4 | b >> 4) as usize] as char);
            text.push(if bytes.len() > 1 {
                ABC[((b & 15) << 2 | c >> 6) as usize] as char
            } else {
                '='
            });
            text.push(if bytes.len() > 2 {
                ABC[(c & 63) as usize] as char
            } else {
                '='
            });
        }
        s.serialize_str(&text)
    }
}
#[cfg(test)]
pub fn bytes_from_json<'de, D: serde::Deserializer<'de>>(d: D) -> Result<Vec<u8>, D::Error> {
    let text = String::deserialize(d)?;
    crate::runner_client::decode_base64(&text).map_err(serde::de::Error::custom)
}

#[cfg(test)]
mod tests {
    use super::*;
    fn value(kind: u8, bytes: &[u8]) -> Vec<u8> {
        let mut out = vec![kind];
        out.extend_from_slice(&(bytes.len() as u32).to_le_bytes());
        out.extend_from_slice(bytes);
        out
    }
    #[test]
    fn documented_porcelain_budgets() {
        let manifest: serde_json::Value =
            serde_json::from_str(include_str!("../../docs/limits.json")).unwrap();
        let expected = std::collections::BTreeMap::from([
            ("porcelain_frame_bytes", LIMIT as u64),
            ("porcelain_decoded_storage_bytes", LIMIT as u64),
            ("porcelain_nesting", DEPTH as u64),
        ]);
        let owned: std::collections::BTreeMap<_, _> = manifest["limits"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|row| {
                row["checks"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .any(|c| c["symbol"] == "documented_porcelain_budgets")
            })
            .map(|row| (row["id"].as_str().unwrap(), row["value"].as_u64().unwrap()))
            .collect();
        assert_eq!(owned, expected);
        assert!(Cursor::new(&[], 32, &Cell::new(LIMIT)).is_ok());
        assert!(Cursor::new(&[], 33, &Cell::new(LIMIT)).is_err());
    }
    #[test]
    fn list_slots_and_nested_strings_share_one_budget() {
        let mut wire = 2u32.to_le_bytes().to_vec();
        wire.extend(value(4, b"abcdefghij"));
        wire.extend(value(4, b"klmnopqrst"));
        let needed = 2 * std::mem::size_of::<String>() + 20;
        assert_eq!(
            Vec::<String>::read_payload(&wire, 1, &Cell::new(needed)).unwrap(),
            ["abcdefghij", "klmnopqrst"]
        );
        assert!(
            Vec::<String>::read_payload(&wire, 1, &Cell::new(needed - 1))
                .unwrap_err()
                .contains("storage budget")
        );
        // Compact valid values cannot demand unconstrained typed slot storage.
        let mut many = 100u32.to_le_bytes().to_vec();
        for _ in 0..100 {
            many.extend(value(4, b""));
        }
        assert!(
            Vec::<String>::read_payload(&many, 1, &Cell::new(100))
                .unwrap_err()
                .contains("storage budget")
        );
    }
    #[test]
    fn native_integer_width_and_boolean_values_are_not_coerced() {
        assert!(i32::read_payload(&i64::MAX.to_le_bytes(), 0, &Cell::new(LIMIT)).is_err());
        assert_eq!(
            u64::read_payload(&u64::MAX.to_le_bytes(), 0, &Cell::new(LIMIT)).unwrap(),
            u64::MAX
        );
        assert!(bool::read_payload(&[2], 0, &Cell::new(LIMIT)).is_err());
        assert!(String::read_payload(&[0xff], 0, &Cell::new(LIMIT)).is_err());
    }

    #[test]
    fn authored_record_faults_are_refused_before_typed_construction() {
        use crate::porcelain_records::PWRunnerTerminationRequest;
        fn field(tag: u16, kind: u8, payload: &[u8]) -> Vec<u8> {
            let mut bytes = tag.to_le_bytes().to_vec();
            bytes.extend(value(kind, payload));
            bytes
        }
        fn frame(id: u16, fields: &[Vec<u8>]) -> Vec<u8> {
            let mut payload = id.to_le_bytes().to_vec();
            for field in fields {
                payload.extend(field);
            }
            let mut bytes = b"PWP1".to_vec();
            bytes.extend(crate::porcelain_records::FINGERPRINT);
            bytes.extend(value(6, &payload));
            bytes
        }
        let signal = field(1, 2, &9i64.to_le_bytes());
        let rc = field(2, 2, &0i64.to_le_bytes());
        let valid = frame(63, &[signal.clone(), rc.clone()]);
        let observed: PWRunnerTerminationRequest = decode(&valid).unwrap();
        assert_eq!((observed.signal, observed.rc, observed.errno), (9, 0, None));
        let faults = [
            frame(64, &[signal.clone(), rc.clone()]),
            frame(63, &[signal.clone()]),
            frame(63, &[signal.clone(), signal.clone(), rc.clone()]),
            frame(63, &[rc.clone(), signal.clone()]),
            frame(
                63,
                &[signal.clone(), rc.clone(), field(4, 2, &0i64.to_le_bytes())],
            ),
            frame(63, &[field(1, 3, &9u64.to_le_bytes()), rc.clone()]),
            frame(63, &[field(1, 2, &i64::MAX.to_le_bytes()), rc]),
        ];
        for fault in faults {
            assert!(decode::<PWRunnerTerminationRequest>(&fault).is_err());
        }
        // Every prefix is incomplete; even complete required fields cannot
        // authorize a record when its announced frame has not arrived.
        for end in 0..valid.len() {
            assert!(decode::<PWRunnerTerminationRequest>(&valid[..end]).is_err());
        }
        let mut length = valid.clone();
        length[37..41].copy_from_slice(&u32::MAX.to_le_bytes());
        assert!(decode::<PWRunnerTerminationRequest>(&length).is_err());
        let mut trailing = valid.clone();
        trailing.push(0);
        assert!(decode::<PWRunnerTerminationRequest>(&trailing).is_err());
        // Version refusal precedes even a simultaneous corrupt root length.
        length[4] ^= 1;
        assert_eq!(
            decode::<PWRunnerTerminationRequest>(&length).unwrap_err(),
            "unsupported porcelain schema"
        );
    }
}
