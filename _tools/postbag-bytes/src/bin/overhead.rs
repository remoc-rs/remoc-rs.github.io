//! What the Full configuration costs per field, by type.
//!
//!     cargo run --bin overhead

use serde::Serialize;

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect::<Vec<_>>().join(" ")
}

/// Encodes one field of the given type and reports both encodings.
macro_rules! show {
    ($name:literal, $ty:ty, $value:expr) => {{
        #[derive(Serialize)]
        struct One {
            #[serde(rename = "_0")]
            v: $ty,
        }
        let v = $value;
        let full = postbag::to_full_vec(&One { v: v.clone() }).unwrap();
        let slim = postbag::to_slim_vec(&One { v }).unwrap();
        println!(
            "{:<18} full {:>2}: {:<44} slim {:>2}: {}",
            $name,
            full.len(),
            hex(&full),
            slim.len(),
            hex(&slim)
        );
    }};
}

#[derive(Serialize, Clone)]
struct Inner {
    #[serde(rename = "_0")]
    a: u8,
}

fn main() {
    println!("A struct with a single field, so the difference is that field's framing.");
    println!("Full = 01 (one field) + identifier + skip length + value\n");

    show!("u32 = 300", u32, 300u32);
    show!("bool", bool, true);
    show!("String \"temp\"", String, "temp".to_string());
    show!("Vec<u8> [1,2,3]", Vec<u8>, vec![1u8, 2, 3]);
    show!("Vec<u16> [1,2,3]", Vec<u16>, vec![1u16, 2, 3]);
    show!("[u8; 3]", [u8; 3], [1u8, 2, 3]);
    show!("bytes (serde_bytes)", serde_bytes::ByteBuf, serde_bytes::ByteBuf::from(vec![1u8, 2, 3]));
    show!("nested struct", Inner, Inner { a: 7 });
    show!("Option<u32>", Option<u32>, Some(300u32));
}
