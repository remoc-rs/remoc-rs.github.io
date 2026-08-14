//! Produces the byte dump shown on the Postbag page, and checks it.
//!
//!     cargo run --manifest-path _tools/postbag-bytes/Cargo.toml
//!
//! Run `cargo test` in this directory to verify that the bytes on the page are
//! still what Postbag produces.

use serde::{Deserialize, Serialize};

/// A unit, to show that enum variants can be numbered too.
#[derive(Debug, PartialEq, Serialize, Deserialize)]
pub enum Unit {
    #[serde(rename = "_0")]
    Celsius,
    #[serde(rename = "_1")]
    Other(String),
}

/// The value shown on the page, with every field numbered.
#[derive(Debug, PartialEq, Serialize, Deserialize)]
pub struct Reading {
    #[serde(rename = "_0")]
    pub sensor: u32,
    #[serde(rename = "_1")]
    pub label: String,
    #[serde(rename = "_2")]
    pub unit: Unit,
}

/// The same value after somebody added a field to it.
#[derive(Debug, PartialEq, Serialize, Deserialize)]
pub struct ReadingV2 {
    #[serde(rename = "_0")]
    pub sensor: u32,
    #[serde(rename = "_1")]
    pub label: String,
    #[serde(rename = "_2")]
    pub unit: Unit,
    #[serde(rename = "_3")]
    pub note: String,
}

pub fn sample() -> Reading {
    Reading { sensor: 300, label: "temp".into(), unit: Unit::Celsius }
}

pub fn sample_v2() -> ReadingV2 {
    ReadingV2 { sensor: 300, label: "temp".into(), unit: Unit::Celsius, note: "roof".into() }
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect::<Vec<_>>().join(" ")
}

fn main() {
    let full = postbag::to_full_vec(&sample()).unwrap();
    let slim = postbag::to_slim_vec(&sample()).unwrap();
    let full_v2 = postbag::to_full_vec(&sample_v2()).unwrap();

    println!("full     ({:2} bytes): {}", full.len(), hex(&full));
    println!("slim     ({:2} bytes): {}", slim.len(), hex(&slim));
    println!("full v2  ({:2} bytes): {}", full_v2.len(), hex(&full_v2));

    // What the page claims about compatibility.
    let back: Reading = postbag::from_full_slice(&full_v2).unwrap();
    println!("\nv2 bytes read as v1: {back:?}  (the unknown field is skipped)");
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The bytes drawn on the page, so that a change in Postbag shows up here.
    #[test]
    fn page_shows_the_real_bytes() {
        assert_eq!(hex(&postbag::to_full_vec(&sample()).unwrap()), include_str!("../full.hex").trim());
        assert_eq!(hex(&postbag::to_slim_vec(&sample()).unwrap()), include_str!("../slim.hex").trim());
    }

    /// A reader of the old type can read data written by the new one.
    #[test]
    fn unknown_fields_are_skipped() {
        let bytes = postbag::to_full_vec(&sample_v2()).unwrap();
        let back: Reading = postbag::from_full_slice(&bytes).unwrap();
        assert_eq!(back, sample());
    }

    /// And the other way round, using the serde default for what is missing.
    #[test]
    fn missing_fields_use_their_default() {
        let bytes = postbag::to_full_vec(&sample()).unwrap();
        let back: ReadingWithDefault = postbag::from_full_slice(&bytes).unwrap();
        assert_eq!(back.note, "");
    }

    #[derive(Deserialize)]
    struct ReadingWithDefault {
        #[serde(rename = "_3", default)]
        note: String,
    }
}
