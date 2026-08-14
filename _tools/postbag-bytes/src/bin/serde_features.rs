//! Which serde attributes actually round-trip through Postbag.
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, PartialEq)]
#[serde(untagged)]
enum Untagged { Nothing(()), Number(u8) }

#[derive(Serialize, Deserialize, Debug, PartialEq)]
#[serde(tag = "kind")]
enum InternallyTagged { A { x: u8 }, B { y: u8 } }

#[derive(Serialize, Deserialize, Debug, PartialEq)]
#[serde(tag = "t", content = "c")]
enum AdjacentlyTagged { A(u8), B(String) }

#[derive(Serialize, Deserialize, Debug, PartialEq)]
struct Inner { a: u8 }

#[derive(Serialize, Deserialize, Debug, PartialEq)]
struct Flattened { #[serde(flatten)] inner: Inner, b: u8 }

#[derive(Serialize, Deserialize, Debug, PartialEq)]
enum ExternallyTagged { A(u8), B { y: u8 } }

fn check<T>(name: &str, value: T)
where T: Serialize + for<'de> Deserialize<'de> + PartialEq + std::fmt::Debug {
    match postbag::to_full_vec(&value) {
        Err(e) => println!("{name:<22} serialize failed: {e}"),
        Ok(bytes) => match postbag::from_full_slice::<T>(&bytes) {
            Ok(back) if back == value => println!("{name:<22} ok ({} bytes)", bytes.len()),
            Ok(_) => println!("{name:<22} ROUND TRIP CHANGED THE VALUE"),
            Err(e) => println!("{name:<22} deserialize failed: {e}"),
        },
    }
}

fn main() {
    check("externally tagged", ExternallyTagged::B { y: 1 });
    check("untagged", Untagged::Number(3));
    check("untagged (unit)", Untagged::Nothing(()));
    check("internally tagged", InternallyTagged::A { x: 1 });
    check("adjacently tagged", AdjacentlyTagged::B("z".into()));
    check("flatten", Flattened { inner: Inner { a: 1 }, b: 2 });
}
