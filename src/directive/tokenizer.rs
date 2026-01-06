//! Tokenizer for directive parsing

use std::iter::Peekable;
use std::str::Chars;

/// Location in source code (line, column)
pub type Loc = (usize, usize);

/// Token kinds
#[derive(Debug, Clone, PartialEq)]
pub enum TokenKind {
    /// End of file
    Eof,
    /// Normal identifier or number
    Normal(String),
    /// Special character(s) like operators, punctuation
    Special(String),
}

/// A token with its location
#[derive(Debug, Clone)]
pub struct Token {
    pub kind: TokenKind,
    pub loc: Loc,
}

impl Token {
    pub fn new(kind: TokenKind, loc: Loc) -> Self {
        Self { kind, loc }
    }

    pub fn eof(loc: Loc) -> Self {
        Self::new(TokenKind::Eof, loc)
    }

    pub fn is_eof(&self) -> bool {
        matches!(self.kind, TokenKind::Eof)
    }

    pub fn is_special(&self) -> bool {
        matches!(self.kind, TokenKind::Special(_))
    }

    pub fn value(&self) -> Option<&str> {
        match &self.kind {
            TokenKind::Normal(s) | TokenKind::Special(s) => Some(s),
            TokenKind::Eof => None,
        }
    }
}

/// Special characters that form operators or punctuation
const SPECIAL_SINGLE: &[char] = &['(', ')', ':', ',', '@', '\n', '\r'];

/// Characters that can be part of multi-character operators
const SPECIAL_OPERATOR: &[char] = &['\\', '=', '<', '>', '/', '+', '!', '*', '~', '|', '&', '^', '-'];

/// Unary operators
const UNARY_OPERATORS: &[char] = &['-', '~'];

/// Tokenizer for directive strings
pub struct Tokenizer<'a> {
    #[allow(dead_code)]
    input: &'a str,
    chars: Peekable<Chars<'a>>,
    pos: usize,
    line: usize,
    column: usize,
    saved_token: Option<Token>,
}

impl<'a> Tokenizer<'a> {
    pub fn new(input: &'a str) -> Self {
        Self {
            input,
            chars: input.chars().peekable(),
            pos: 0,
            line: 1,
            column: 1,
            saved_token: None,
        }
    }

    fn peek_char(&mut self) -> Option<char> {
        self.chars.peek().copied()
    }

    fn next_char(&mut self) -> Option<char> {
        let c = self.chars.next()?;
        self.pos += c.len_utf8();
        if c == '\n' {
            self.line += 1;
            self.column = 1;
        } else {
            self.column += 1;
        }
        Some(c)
    }

    fn skip_whitespace(&mut self) {
        while let Some(c) = self.peek_char() {
            if c.is_whitespace() && c != '\n' && c != '\r' {
                self.next_char();
            } else {
                break;
            }
        }
    }

    fn is_special_single(c: char) -> bool {
        SPECIAL_SINGLE.contains(&c)
    }

    fn is_special_operator(c: char) -> bool {
        SPECIAL_OPERATOR.contains(&c)
    }

    fn read_normal(&mut self) -> String {
        let mut result = String::new();
        while let Some(c) = self.peek_char() {
            if c.is_whitespace() || Self::is_special_single(c) || Self::is_special_operator(c) {
                break;
            }
            result.push(self.next_char().unwrap());
        }
        result
    }

    fn read_operator(&mut self) -> String {
        let mut result = String::new();
        while let Some(c) = self.peek_char() {
            if Self::is_special_operator(c) {
                result.push(self.next_char().unwrap());
            } else {
                break;
            }
        }
        result
    }
}

impl<'a> Iterator for Tokenizer<'a> {
    type Item = Token;

    fn next(&mut self) -> Option<Self::Item> {
        // Return saved token if any
        if let Some(token) = self.saved_token.take() {
            // Handle splitting of operator + unary
            if let TokenKind::Special(ref s) = token.kind {
                if s.len() > 1 {
                    let last_char = s.chars().last().unwrap();
                    if UNARY_OPERATORS.contains(&last_char) {
                        // Split: return first part, save the unary
                        let first_part = &s[..s.len() - last_char.len_utf8()];
                        let (line, col) = token.loc;
                        self.saved_token = Some(Token::new(
                            TokenKind::Special(last_char.to_string()),
                            (line, col + first_part.len()),
                        ));
                        return Some(Token::new(
                            TokenKind::Special(first_part.to_string()),
                            token.loc,
                        ));
                    }
                }
            }
            return Some(token);
        }

        self.skip_whitespace();

        let loc = (self.line, self.column);

        let c = self.peek_char()?;

        // Handle newline specially - skip it and continue
        if c == '\n' || c == '\r' {
            self.next_char();
            if c == '\r' {
                if self.peek_char() == Some('\n') {
                    self.next_char();
                }
            }
            return self.next();
        }

        // Single special character
        if Self::is_special_single(c) {
            self.next_char();
            return Some(Token::new(TokenKind::Special(c.to_string()), loc));
        }

        // Operator sequence
        if Self::is_special_operator(c) {
            let op = self.read_operator();
            let token = Token::new(TokenKind::Special(op.clone()), loc);

            // Check if we need to split for unary operator
            if op.len() > 1 {
                let last_char = op.chars().last().unwrap();
                if UNARY_OPERATORS.contains(&last_char) {
                    self.saved_token = Some(token);
                    return self.next();
                }
            }

            return Some(token);
        }

        // Normal token (identifier, number, etc.)
        let value = self.read_normal();
        if value.is_empty() {
            return Some(Token::eof(loc));
        }

        // Trim trailing whitespace from normal tokens
        let trimmed = value.trim_end();
        Some(Token::new(TokenKind::Normal(trimmed.to_string()), loc))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_command() {
        let mut tokenizer = Tokenizer::new("ma:20");
        assert!(matches!(tokenizer.next().unwrap().kind, TokenKind::Normal(s) if s == "ma"));
        assert!(matches!(tokenizer.next().unwrap().kind, TokenKind::Special(s) if s == ":"));
        assert!(matches!(tokenizer.next().unwrap().kind, TokenKind::Normal(s) if s == "20"));
    }

    #[test]
    fn test_command_with_series() {
        let mut tokenizer = Tokenizer::new("ma:20@close");
        assert!(matches!(tokenizer.next().unwrap().kind, TokenKind::Normal(s) if s == "ma"));
        assert!(matches!(tokenizer.next().unwrap().kind, TokenKind::Special(s) if s == ":"));
        assert!(matches!(tokenizer.next().unwrap().kind, TokenKind::Normal(s) if s == "20"));
        assert!(matches!(tokenizer.next().unwrap().kind, TokenKind::Special(s) if s == "@"));
        assert!(matches!(tokenizer.next().unwrap().kind, TokenKind::Normal(s) if s == "close"));
    }

    #[test]
    fn test_operator() {
        let mut tokenizer = Tokenizer::new("a // b");
        assert!(matches!(tokenizer.next().unwrap().kind, TokenKind::Normal(s) if s == "a"));
        assert!(matches!(tokenizer.next().unwrap().kind, TokenKind::Special(s) if s == "//"));
        assert!(matches!(tokenizer.next().unwrap().kind, TokenKind::Normal(s) if s == "b"));
    }
}

