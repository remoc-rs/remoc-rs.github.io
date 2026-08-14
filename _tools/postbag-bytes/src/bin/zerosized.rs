//! Do sequences of zero-sized elements survive? Their length cannot be derived
//! from the number of bytes they occupy.
use serde::Serialize;

fn hex(b: &[u8]) -> String { b.iter().map(|x| format!("{x:02x}")).collect::<Vec<_>>().join(" ") }

#[derive(Serialize, Clone, PartialEq, Debug)]
struct Empty;

fn main() {
    let units: Vec<()> = vec![(), (), ()];
    let empties = vec![Empty, Empty, Empty];
    println!("Vec<()> x3      full: {}", hex(&postbag::to_full_vec(&units).unwrap()));
    println!("Vec<Empty> x3   full: {}", hex(&postbag::to_full_vec(&empties).unwrap()));
    println!("Vec<u8> [1,2,3] full: {}", hex(&postbag::to_full_vec(&vec![1u8,2,3]).unwrap()));
    let back: Vec<()> = postbag::from_full_slice(&postbag::to_full_vec(&units).unwrap()).unwrap();
    println!("Vec<()> round trip: {} elements", back.len());
}
