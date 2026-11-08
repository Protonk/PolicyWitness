//! Closed binary primitives. Records are generated; semantic admission is separate.
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub const LIMIT: usize = 128 * 1024 * 1024;
const DEPTH: usize = 32;
pub trait WireRead: Sized {
    const KIND: u8;
    fn read_payload(data: &[u8], depth: usize) -> Result<Self, String>;
}

#[derive(Clone, Copy)]
pub struct WireValue<'a> { kind: u8, data: &'a [u8], depth: usize }
impl WireValue<'_> {
    pub fn decode<T: WireRead>(self) -> Result<T, String> {
        if self.kind != T::KIND { return Err("wrong scalar/record kind".into()); }
        T::read_payload(self.data, self.depth)
    }
    pub fn bytes(self) -> Result<Vec<u8>, String> {
        if self.kind != 5 { return Err("expected bytes".into()); }
        let mut data = Vec::new();
        data.try_reserve_exact(self.data.len()).map_err(|_| "bytes allocation")?;
        data.extend_from_slice(self.data); Ok(data)
    }
}
struct Cursor<'a> { data: &'a [u8], offset: usize, depth: usize }
impl<'a> Cursor<'a> {
    fn new(data: &'a [u8], depth: usize) -> Result<Self,String> {
        if depth > DEPTH || data.len() > LIMIT { return Err("wire budget".into()); }
        Ok(Self {data, offset:0, depth})
    }
    fn take(&mut self, count: usize) -> Result<&'a [u8],String> {
        let end=self.offset.checked_add(count).ok_or("length overflow")?;
        let bytes=self.data.get(self.offset..end).ok_or("short wire value")?;
        self.offset=end; Ok(bytes)
    }
    fn u16(&mut self) -> Result<u16,String> { Ok(u16::from_le_bytes(self.take(2)?.try_into().unwrap())) }
    fn count(&mut self, minimum:usize) -> Result<usize,String> {
        let count=u32::from_le_bytes(self.take(4)?.try_into().unwrap()) as usize;
        if count > (self.data.len()-self.offset)/minimum { return Err("impossible collection count".into()); }
        Ok(count)
    }
    fn value(&mut self) -> Result<WireValue<'a>,String> {
        let kind=self.take(1)?[0];
        if !(1..=9).contains(&kind) { return Err("unknown wire kind".into()); }
        let len=u32::from_le_bytes(self.take(4)?.try_into().unwrap()) as usize;
        let data=self.take(len)?;
        if self.depth >= DEPTH { return Err("wire depth".into()); }
        Ok(WireValue {kind,data,depth:self.depth+1})
    }
    fn finish(&self)->Result<(),String> {
        if self.offset==self.data.len() {Ok(())} else {Err("trailing wire data".into())}
    }
}
pub struct RecordReader<'a> { cursor:Cursor<'a>, last:u16 }
impl<'a> RecordReader<'a> {
    pub fn new(data:&'a[u8], id:u16, depth:usize)->Result<Self,String> {
        let mut cursor=Cursor::new(data,depth)?;
        if cursor.u16()? != id {return Err("wrong record identity".into());}
        Ok(Self {cursor,last:0})
    }
    pub fn next(&mut self)->Result<Option<(u16,WireValue<'a>)>,String> {
        if self.cursor.offset==self.cursor.data.len() {return Ok(None);}
        let tag=self.cursor.u16()?;
        if tag<=self.last {return Err("duplicate or unordered field tag".into());}
        self.last=tag;Ok(Some((tag,self.cursor.value()?)))
    }
}
pub fn decode<T:WireRead>(data:&[u8])->Result<T,String> {
    if data.len()>LIMIT || data.get(..4)!=Some(b"PWP1") {return Err("invalid porcelain frame".into());}
    if data.get(4..36)!=Some(&crate::porcelain_records::FINGERPRINT) {return Err("unsupported porcelain schema".into());}
    let mut reader=Cursor::new(&data[36..],0)?;
    let value=reader.value()?;reader.finish()?;value.decode()
}
pub fn variant(data:&[u8],depth:usize)->Result<(u16,WireValue<'_>),String> {
    let mut reader=Cursor::new(data,depth)?;let tag=reader.u16()?;
    let value=reader.value()?;reader.finish()?;Ok((tag,value))
}
impl WireRead for bool {
    const KIND:u8=1;
    fn read_payload(data:&[u8],_:usize)->Result<Self,String> {
        match data { [0]=>Ok(false), [1]=>Ok(true), _=>Err("invalid boolean".into()) }
    }
}
macro_rules! integer {
    ($t:ty,$wire:ty,$kind:expr) => {
        impl WireRead for $t {
            const KIND:u8=$kind;
            fn read_payload(data:&[u8],_:usize)->Result<Self,String> {
                let bytes: [u8;8]=data.try_into().map_err(|_|"integer width")?;
                Self::try_from(<$wire>::from_le_bytes(bytes)).map_err(|_|"integer range".into())
            }
        }
    }
}
integer!(i32,i64,2);integer!(i64,i64,2);integer!(u32,u64,3);integer!(u64,u64,3);
impl WireRead for String {
    const KIND:u8=4;
    fn read_payload(data:&[u8],_:usize)->Result<Self,String> {
        let text=std::str::from_utf8(data).map_err(|_|"invalid UTF-8")?;
        let mut result=String::new();result.try_reserve_exact(text.len()).map_err(|_|"text allocation")?;
        result.push_str(text);Ok(result)
    }
}
impl<T:WireRead> WireRead for Vec<T> {
    const KIND:u8=7;
    fn read_payload(data:&[u8],depth:usize)->Result<Self,String> {
        let mut reader=Cursor::new(data,depth)?;let count=reader.count(5)?;
        let mut output=Vec::new();output.try_reserve_exact(count).map_err(|_|"list allocation")?;
        for _ in 0..count {output.push(reader.value()?.decode()?);}
        reader.finish()?;Ok(output)
    }
}
impl<T:WireRead> WireRead for BTreeMap<String,T> {
    const KIND:u8=8;
    fn read_payload(data:&[u8],depth:usize)->Result<Self,String> {
        let mut reader=Cursor::new(data,depth)?;let count=reader.count(10)?;
        let mut output=BTreeMap::new();
        for _ in 0..count {
            let key:String=reader.value()?.decode()?;
            if output.last_key_value().is_some_and(|(last,_)|last>=&key) {return Err("duplicate or unordered map key".into());}
            output.insert(key,reader.value()?.decode()?);
        }
        reader.finish()?;Ok(output)
    }
}
// Base64 exists exclusively at the public JSON byte projection and authored JSON
// fixture boundary. No internal field is converted through text for access.
pub struct Base64<'a>(pub &'a [u8]);
impl Serialize for Base64<'_> {
    fn serialize<S:serde::Serializer>(&self,s:S)->Result<S::Ok,S::Error> {
        const ABC:&[u8;64]=b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        let mut text=String::with_capacity(self.0.len().div_ceil(3)*4);
        for bytes in self.0.chunks(3) {
            let a=bytes[0];let b=bytes.get(1).copied().unwrap_or(0);let c=bytes.get(2).copied().unwrap_or(0);
            text.push(ABC[(a>>2) as usize] as char);text.push(ABC[((a&3)<<4|b>>4) as usize] as char);
            text.push(if bytes.len()>1 {ABC[((b&15)<<2|c>>6) as usize] as char} else {'='});
            text.push(if bytes.len()>2 {ABC[(c&63) as usize] as char} else {'='});
        }
        s.serialize_str(&text)
    }
}
pub fn bytes_from_json<'de,D:serde::Deserializer<'de>>(d:D)->Result<Vec<u8>,D::Error> {
    let text=String::deserialize(d)?;
    crate::runner_client::decode_base64(&text).map_err(serde::de::Error::custom)
}
