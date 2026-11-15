//! The `run` result a selection determines. `build.rs` includes this file to
//! render the result card through the constructor `run` uses.

use crate::interface::result::Selection;
use crate::json_contract::JsonResult;

pub fn run_result(selection: &Selection, error: Option<String>) -> JsonResult {
    JsonResult::new(
        selection.ok,
        selection.exit,
        Some(&selection.outcome),
        error,
    )
}
