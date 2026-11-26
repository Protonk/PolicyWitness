//! Runner management forms, record selectors and the decision reported by removal.

use std::ffi::OsStr;

enumerated!(RunnerForm {
    List,
    Status,
    Reconcile,
    Verify,
    Install,
    Validate,
    Remove
});

impl RunnerForm {
    pub const fn spelling(self) -> &'static str {
        match self {
            Self::List => "list",
            Self::Status => "status",
            Self::Reconcile => "reconcile",
            Self::Verify => "verify",
            Self::Install => "install",
            Self::Validate => "validate",
            Self::Remove => "remove",
        }
    }

    pub fn recognize_form(word: &OsStr) -> Option<Self> {
        Self::ALL
            .iter()
            .copied()
            .find(|form| word == form.spelling())
    }

    pub fn invocation(self) -> String {
        format!(
            "{} {}",
            super::commands::Command::Runner.def().spelling,
            self.spelling()
        )
    }

    pub fn with_selector(self, selector: Selector, value: &str) -> String {
        format!("{} {} {value}", self.invocation(), selector.spelling())
    }

    pub const fn takes_selector(self) -> bool {
        matches!(self, Self::Status | Self::Verify | Self::Remove)
    }

    pub const fn takes_arguments(self) -> bool {
        self.takes_selector() || matches!(self, Self::Install)
    }

    #[allow(dead_code)] // Read by the build script when it renders the card.
    pub const fn description(self) -> &'static str {
        match self {
            Self::List => "List registered runners and pending cleanup records.",
            Self::Status => "Read one registered runner.",
            Self::Reconcile => {
                "Inspect service and plist presence and ownership without changing them."
            }
            Self::Verify => "Send a fixed verification request to the selected runner.",
            Self::Install => "Register an XPC bundle and prepare its launchd service.",
            Self::Validate => "Refresh the registry with signature and entitlement observations.",
            Self::Remove => "Remove the selected installation or retry its pending cleanup.",
        }
    }
}

enumerated!(Selector { Id, ServiceName });

impl Selector {
    pub const fn spelling(self) -> &'static str {
        match self {
            Self::Id => "--id",
            Self::ServiceName => "--service-name",
        }
    }

    #[allow(dead_code)] // Read by the build script when it renders the card.
    pub const fn operand(self) -> &'static str {
        match self {
            Self::Id => "<runner-id>",
            Self::ServiceName => "<service-name>",
        }
    }

    pub fn recognize_selector(word: &OsStr) -> Option<Self> {
        Self::ALL
            .iter()
            .copied()
            .find(|selector| word == selector.spelling())
    }
}

enumerated!(
    /// A removal can return success with either disposition.
    Removal { Complete, Retained }
);

impl Removal {
    #[allow(dead_code)] // Read by the build script when it renders the card.
    pub const FIELD: &'static str = "data.cleanup_retained";

    pub fn from_complete(complete: bool) -> Self {
        if complete {
            Self::Complete
        } else {
            Self::Retained
        }
    }

    pub const fn retained(self) -> bool {
        matches!(self, Self::Retained)
    }

    #[allow(dead_code)] // Read by the build script when it renders the card.
    pub const fn guidance(self) -> &'static [&'static str] {
        match self {
            Self::Complete => &[
                "Discard staging. The service and plist were observed absent and cleanup was saved.",
            ],
            Self::Retained => &[
                "Keep the staged bundle and ownership record. Read data.warnings and data.retained_record.",
                "Find the pending record and inspect service and plist ownership.",
                "Retry with its recorded selector when the remaining resources are owned or absent.",
            ],
        }
    }
}
