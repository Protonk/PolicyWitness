//! SHA-256 as lowercase hex: the one spelling every controller hash uses,
//! shared with the sbpl-check helper through a `#[path]` include.

use sha2::{Digest, Sha256};

pub fn sha256_hex(bytes: impl AsRef<[u8]>) -> String {
    format!("{:x}", Sha256::digest(bytes.as_ref()))
}
