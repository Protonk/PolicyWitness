//! The definitions that govern the command line and the run result.
//!
//! Dispatch, help selection, `run`'s argument parsing, every reader of the
//! runner-kind vocabulary and run result selection consume these tables.
//! `build.rs` includes the same files to render the help cards and write the
//! interface inventory, so a card states a spelling only because the code
//! that admits it holds that spelling. The module uses `std` alone.

/// An enum whose `ALL` lists every variant in declaration order.
macro_rules! enumerated {
    ($(#[$meta:meta])* $name:ident { $($(#[$variant_meta:meta])* $variant:ident),+ $(,)? }) => {
        $(#[$meta])*
        #[derive(Clone, Copy, Debug, PartialEq, Eq)]
        pub enum $name { $($(#[$variant_meta])* $variant),+ }
        impl $name {
            // build.rs enumerates tables the binary only indexes.
            #[allow(dead_code)]
            pub const ALL: &'static [$name] = &[$($name::$variant),+];
        }
    };
}

pub mod commands;
pub mod result;
pub mod run_args;
pub mod runner_kind;
