//! The runner-kind vocabulary and its readers.

enumerated!(
    /// The kind a runner record or selection carries.
    Kind {
        Standard,
        Byoxpc,
    }
);

enumerated!(
    /// A site that reads a kind from text.
    Reader {
        /// `run --runner-mode <word>`.
        RunOption,
        /// The request's `runner.mode`.
        RequestSelector,
        /// `runner install --kind <word>`.
        InstallOption,
        /// A stored registry record's `kind`.
        Registry,
    }
);

enumerated!(
    /// A spelling some reader recognizes.
    Word {
        Standard,
        Byoxpc,
        Machme,
        Debuggable,
    }
);

/// What a reader does with a word it recognizes.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Rule {
    /// The word is accepted as its kind.
    Admits,
    /// The reader resolves the word to its kind.
    Alias,
}

impl Word {
    pub const fn spelling(self) -> &'static str {
        match self {
            Word::Standard => "standard",
            Word::Byoxpc => "byoxpc",
            Word::Machme => "machme",
            Word::Debuggable => "debuggable",
        }
    }

    /// The kind the word names or resolves to.
    pub const fn kind(self) -> Kind {
        match self {
            Word::Standard => Kind::Standard,
            Word::Byoxpc | Word::Machme | Word::Debuggable => Kind::Byoxpc,
        }
    }

    /// `None` where the reader does not recognize the word.
    pub const fn rule(self, reader: Reader) -> Option<Rule> {
        match (self, reader) {
            (Word::Standard | Word::Byoxpc, _) => Some(Rule::Admits),
            (Word::Machme | Word::Debuggable, Reader::Registry) => Some(Rule::Alias),
            (Word::Machme | Word::Debuggable, _) => None,
        }
    }
}

impl Kind {
    /// The word that names the kind wherever it is written.
    pub const fn word(self) -> Word {
        match self {
            Kind::Standard => Word::Standard,
            Kind::Byoxpc => Word::Byoxpc,
        }
    }

    pub const fn as_str(self) -> &'static str {
        self.word().spelling()
    }
}

impl Reader {
    /// The kind a value names for this reader; `None` for a value the
    /// reader does not recognize.
    pub fn resolve(self, value: &str) -> Option<Kind> {
        let word = Word::ALL
            .iter()
            .copied()
            .find(|word| word.spelling() == value)?;
        match word.rule(self)? {
            Rule::Admits | Rule::Alias => Some(word.kind()),
        }
    }
}
