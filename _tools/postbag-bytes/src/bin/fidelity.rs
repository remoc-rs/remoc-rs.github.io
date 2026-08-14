//! Checks that values survive a round trip unchanged, including the ones that
//! text formats have to mangle.
//!
//!     cargo run --bin fidelity

use std::collections::{BTreeMap, HashMap};

use serde::{Deserialize, Serialize};

fn round_trip<T>(name: &str, value: T)
where
    T: Serialize + for<'de> Deserialize<'de> + PartialEq + std::fmt::Debug,
{
    let full: T = postbag::from_full_slice(&postbag::to_full_vec(&value).unwrap()).unwrap();
    let slim: T = postbag::from_slim_slice(&postbag::to_slim_vec(&value).unwrap()).unwrap();
    let bytes = postbag::to_full_vec(&value).unwrap();
    assert_eq!(full, value, "{name} did not survive Full");
    assert_eq!(slim, value, "{name} did not survive Slim");
    println!("{name:<34} {:>3} bytes  ok", bytes.len());
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct Unit;

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct Newtype(u8);

#[derive(Debug, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
enum Key {
    A,
    B(u8),
}

fn main() {
    // The one text formats get wrong: an absent value inside a present one.
    round_trip("None", Option::<Option<u32>>::None);
    round_trip("Some(None)", Some(Option::<u32>::None));
    round_trip("Some(Some(0))", Some(Some(0u32)));

    // Integers that do not fit a double.
    round_trip("u128::MAX", u128::MAX);
    round_trip("i128::MIN", i128::MIN);
    round_trip("u64::MAX", u64::MAX);

    // Keys that are not strings.
    round_trip("map keyed by a tuple", BTreeMap::from([((1u8, 2u8), "x".to_string())]));
    round_trip("map keyed by an enum", BTreeMap::from([(Key::B(3), 1u8)]));
    round_trip("map keyed by a string", HashMap::from([("a".to_string(), 1u8)]));

    // Shapes serde has but JSON does not.
    round_trip("unit struct", Unit);
    round_trip("newtype struct", Newtype(7));
    round_trip("tuple", (1u8, "two".to_string(), 3.5f64));
    round_trip("enum with data", Key::B(9));
    round_trip("char", '🦑');
    round_trip("byte array", [0u8, 255, 128]);

    // Floats, exactly.
    round_trip("f32 fraction", 0.1f32);
    round_trip("f64 fraction", 0.1f64);
    round_trip("f64 negative zero", -0.0f64);
    let nan: f64 = f64::NAN;
    let back: f64 = postbag::from_full_slice(&postbag::to_full_vec(&nan).unwrap()).unwrap();
    println!("{:<34} {:>3} bytes  {}", "f64 NaN", 8, if back.is_nan() { "ok" } else { "LOST" });
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The claims the page makes about fidelity, checked.
    #[test]
    fn values_survive_a_round_trip() {
        // An absent value inside a present one stays distinguishable, which a
        // format with only `null` cannot manage.
        assert_ne!(
            postbag::to_full_vec(&Some(Option::<u32>::None)).unwrap(),
            postbag::to_full_vec(&Option::<Option<u32>>::None).unwrap()
        );
        let some_none: Option<Option<u32>> =
            postbag::from_full_slice(&postbag::to_full_vec(&Some(Option::<u32>::None)).unwrap()).unwrap();
        assert_eq!(some_none, Some(None));

        // Integers wider than a double.
        let big: u128 =
            postbag::from_full_slice(&postbag::to_full_vec(&u128::MAX).unwrap()).unwrap();
        assert_eq!(big, u128::MAX);

        // Map keys that are not strings.
        let keyed = BTreeMap::from([((1u8, 2u8), "x".to_string())]);
        let back: BTreeMap<(u8, u8), String> =
            postbag::from_full_slice(&postbag::to_full_vec(&keyed).unwrap()).unwrap();
        assert_eq!(back, keyed);

        // And a NaN is still a NaN.
        let nan: f64 = postbag::from_full_slice(&postbag::to_full_vec(&f64::NAN).unwrap()).unwrap();
        assert!(nan.is_nan());
    }
}
