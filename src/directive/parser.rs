//! Recursive descent parser for directive syntax

use super::tokenizer::{Token, Tokenizer, Loc};
use super::types::*;
use crate::errors::{DirectiveError, DirectiveResult};

use regex::Regex;
use once_cell::sync::Lazy;

static REGEX_DOT_WHITESPACES: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"\.\s*").unwrap()
});

static REGEX_NUMBER: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^(\d+)?(?P<frac>\.\d+)?$").unwrap()
});

/// Operator priority levels (higher = binds tighter)
#[derive(Debug, Clone, Copy)]
struct OperatorInfo {
    priority: i32,
}

fn get_operator_info(name: &str) -> Option<OperatorInfo> {
    match name {
        "|" => Some(OperatorInfo { priority: 1 }),
        "^" => Some(OperatorInfo { priority: 2 }),
        "&" => Some(OperatorInfo { priority: 3 }),
        "<" | "<=" | ">=" | ">" => Some(OperatorInfo { priority: 4 }),
        "==" | "!=" => Some(OperatorInfo { priority: 5 }),
        "//" | "\\" | "><" => Some(OperatorInfo { priority: 6 }),
        "+" | "-" => Some(OperatorInfo { priority: 7 }),
        "*" | "/" => Some(OperatorInfo { priority: 8 }),
        _ => None,
    }
}

fn get_unary_operator_info(name: &str) -> Option<OperatorInfo> {
    match name {
        "-" | "~" => Some(OperatorInfo { priority: 9 }),
        _ => None,
    }
}

/// Parser for directive strings
pub struct Parser<'a> {
    tokens: std::iter::Peekable<Tokenizer<'a>>,
    current: Token,
    prev: Token,
    lookahead: Option<Token>,
}

impl<'a> Parser<'a> {
    pub fn new(input: &'a str) -> Self {
        let mut tokenizer = Tokenizer::new(input);
        let first_token = tokenizer.next().unwrap_or_else(|| Token::eof((1, 1)));

        Self {
            tokens: tokenizer.peekable(),
            current: first_token.clone(),
            prev: first_token,
            lookahead: None,
        }
    }

    fn next_token(&mut self) {
        self.prev = self.current.clone();

        if let Some(token) = self.lookahead.take() {
            self.current = token;
            return;
        }

        self.current = self.tokens.next().unwrap_or_else(|| Token::eof((1, 1)));
    }

    fn look_back(&mut self) {
        self.lookahead = Some(self.current.clone());
        self.current = self.prev.clone();
    }

    fn is_at(&self, value: &str) -> bool {
        self.current.value() == Some(value)
    }

    fn expect(&self, value: &str) -> DirectiveResult<()> {
        if self.current.is_eof() {
            return Err(DirectiveError::SyntaxError {
                line: self.current.loc.0,
                column: self.current.loc.1,
                message: "unexpected EOF".to_string(),
            });
        }

        if !self.is_at(value) {
            return Err(DirectiveError::SyntaxError {
                line: self.current.loc.0,
                column: self.current.loc.1,
                message: format!("expected '{}', got '{}'",
                    value,
                    self.current.value().unwrap_or("EOF")),
            });
        }

        Ok(())
    }

    fn unexpected(&self) -> DirectiveError {
        DirectiveError::SyntaxError {
            line: self.current.loc.0,
            column: self.current.loc.1,
            message: format!("unexpected token '{}'",
                self.current.value().unwrap_or("EOF")),
        }
    }

    pub fn parse(&mut self) -> DirectiveResult<ExpressionNode> {
        let directive = self.parse_expression(1)?; // Start with lowest priority (1)

        if !self.current.is_eof() {
            return Err(DirectiveError::SyntaxError {
                line: self.current.loc.0,
                column: self.current.loc.1,
                message: format!("expected EOF, got '{}'",
                    self.current.value().unwrap_or("?")),
            });
        }

        Ok(directive)
    }

    fn parse_expression(&mut self, min_priority: i32) -> DirectiveResult<ExpressionNode> {
        if min_priority > 8 {
            return self.parse_primary_expression();
        }

        let mut left = self.parse_expression(min_priority + 1)?;

        while let Some(op_info) = self.detect_operator(min_priority) {
            let operator = OperatorNode {
                loc: self.prev.loc,
                name: self.prev.value().unwrap_or("").to_string(),
                priority: op_info.priority,
            };

            let right = self.parse_expression(min_priority + 1)?;

            left = ExpressionNode::Binary {
                loc: left.loc(),
                operator,
                left: Box::new(left),
                right: Box::new(right),
            };
        }

        Ok(left)
    }

    fn detect_operator(&mut self, priority: i32) -> Option<OperatorInfo> {
        if self.current.is_eof() || !self.current.is_special() {
            return None;
        }

        let name = self.current.value()?;
        let info = get_operator_info(name)?;

        if info.priority != priority {
            return None;
        }

        self.next_token();
        Some(info)
    }

    fn parse_primary_expression(&mut self) -> DirectiveResult<ExpressionNode> {
        if self.current.is_eof() {
            return Err(DirectiveError::SyntaxError {
                line: self.current.loc.0,
                column: self.current.loc.1,
                message: "unexpected EOF".to_string(),
            });
        }

        let loc = self.current.loc;
        let unary_name = self.current.value().map(|s| s.to_string());

        // Check for unary operator
        if let Some(ref name) = unary_name {
            if let Some(info) = get_unary_operator_info(name) {
                self.next_token();

                // Check for positive number after minus
                let number = self.detect_positive_number();

                if name == "-" {
                    if let Some(num) = number {
                        // Negate the number
                        let neg_num = match num {
                            Primitive::Int(i) => Primitive::Int(-i),
                            Primitive::Float(f) => Primitive::Float(-f),
                            _ => num,
                        };
                        return Ok(ExpressionNode::Scalar(ScalarNode {
                            loc,
                            value: neg_num,
                        }));
                    }
                } else if name == "~" && number.is_some() {
                    // ~ followed by number is invalid
                    self.look_back();
                    return Err(self.unexpected());
                }

                let expression = self.parse_primary_directive()?;

                return Ok(ExpressionNode::Unary {
                    loc,
                    operator: OperatorNode {
                        loc,
                        name: name.clone(),
                        priority: info.priority,
                    },
                    expression: Box::new(expression),
                });
            }
        }

        // Check for number
        if let Some(num) = self.detect_positive_number() {
            return Ok(ExpressionNode::Scalar(ScalarNode {
                loc,
                value: num,
            }));
        }

        self.parse_primary_directive()
    }

    fn detect_positive_number(&mut self) -> Option<Primitive> {
        if self.current.is_eof() || self.current.is_special() {
            return None;
        }

        let value = self.current.value()?.to_string();
        let captures = REGEX_NUMBER.captures(&value)?;

        self.next_token();

        if captures.name("frac").is_some() {
            value.parse::<f64>().ok().map(Primitive::Float)
        } else {
            value.parse::<i64>().ok().map(Primitive::Int)
        }
    }

    fn detect_number(&mut self) -> Option<Primitive> {
        let is_minus = self.is_at("-");
        if is_minus {
            self.next_token();
        }

        if let Some(num) = self.detect_positive_number() {
            return Some(if is_minus {
                match num {
                    Primitive::Int(i) => Primitive::Int(-i),
                    Primitive::Float(f) => Primitive::Float(-f),
                    other => other,
                }
            } else {
                num
            });
        }

        if is_minus {
            self.look_back();
        }

        None
    }

    fn parse_primary_directive(&mut self) -> DirectiveResult<ExpressionNode> {
        if self.is_at("(") {
            return self.parse_wrapped_directive();
        }

        self.parse_command()
    }

    fn parse_wrapped_directive(&mut self) -> DirectiveResult<ExpressionNode> {
        self.next_token(); // consume '('
        let directive = self.parse_expression(1)?;
        self.expect(")")?;
        self.next_token(); // consume ')'
        Ok(directive)
    }

    fn parse_command(&mut self) -> DirectiveResult<ExpressionNode> {
        let loc = self.current.loc;
        let (name, sub) = self.parse_command_name()?;

        let args = if self.is_at(":") {
            self.next_token();
            self.parse_args()?
        } else {
            Vec::new()
        };

        let series = if self.is_at("@") {
            self.next_token();
            self.parse_series()?
        } else {
            Vec::new()
        };

        Ok(ExpressionNode::Command(CommandNode {
            loc,
            name,
            sub,
            args,
            series,
        }))
    }

    fn parse_command_name(&mut self) -> DirectiveResult<(String, Option<String>)> {
        if self.current.is_eof() {
            return Err(DirectiveError::SyntaxError {
                line: self.current.loc.0,
                column: self.current.loc.1,
                message: "unexpected EOF".to_string(),
            });
        }

        if self.current.is_special() {
            return Err(self.unexpected());
        }

        let text = self.current.value().unwrap_or("").to_string();

        self.next_token();

        // Check for dot in name
        if let Some(captures) = REGEX_DOT_WHITESPACES.find(&text) {
            let start = captures.start();
            let end = captures.end();
            let name = text[..start].to_string();
            let sub = text[end..].to_string();
            Ok((name, Some(sub)))
        } else {
            Ok((text, None))
        }
    }

    fn parse_args(&mut self) -> DirectiveResult<Vec<ArgumentNode>> {
        let mut args = Vec::new();
        let mut has_arg;

        loop {
            if self.current.is_eof() {
                break;
            }

            let loc = self.current.loc;
            let number = self.detect_number();

            if let Some(num) = number {
                args.push(ArgumentNode {
                    loc,
                    value: Some(num),
                });
                has_arg = true;
            } else if !self.current.is_special() {
                let value = self.current.value().unwrap_or("").to_string();
                self.next_token();
                args.push(ArgumentNode {
                    loc,
                    value: Some(Primitive::String(value)),
                });
                has_arg = true;
            } else {
                has_arg = false;
            }

            if self.is_at(",") {
                if !has_arg {
                    // Empty argument (default value)
                    args.push(ArgumentNode {
                        loc,
                        value: None,
                    });
                }
                self.next_token();
            } else {
                break;
            }
        }

        Ok(args)
    }

    fn parse_series(&mut self) -> DirectiveResult<Vec<SeriesArgumentNode>> {
        let mut series = Vec::new();
        let mut has_series;

        loop {
            let loc = self.current.loc;

            if self.is_at("(") {
                // Nested directive
                let directive = self.parse_wrapped_directive()?;
                series.push(SeriesArgumentNode::Directive(loc, Box::new(directive)));
                has_series = true;
            } else if !self.current.is_special() && !self.current.is_eof() {
                let value = self.current.value().unwrap_or("").to_string();
                self.next_token();
                series.push(SeriesArgumentNode::Column(loc, value));
                has_series = true;
            } else {
                has_series = false;
            }

            if self.is_at(",") {
                if !has_series {
                    // Empty series argument (default value)
                    series.push(SeriesArgumentNode::Empty(loc));
                }
                self.next_token();
            } else {
                break;
            }
        }

        Ok(series)
    }
}

impl ExpressionNode {
    pub fn loc(&self) -> Loc {
        match self {
            ExpressionNode::Scalar(s) => s.loc,
            ExpressionNode::Command(c) => c.loc,
            ExpressionNode::Binary { loc, .. } => *loc,
            ExpressionNode::Unary { loc, .. } => *loc,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_simple_command() {
        let mut parser = Parser::new("ma:20");
        let result = parser.parse().unwrap();
        if let ExpressionNode::Command(cmd) = result {
            assert_eq!(cmd.name, "ma");
            assert_eq!(cmd.args.len(), 1);
        } else {
            panic!("Expected Command node");
        }
    }

    #[test]
    fn test_parse_command_with_sub() {
        let mut parser = Parser::new("kdj.k:9,3");
        let result = parser.parse().unwrap();
        if let ExpressionNode::Command(cmd) = result {
            assert_eq!(cmd.name, "kdj");
            assert_eq!(cmd.sub, Some("k".to_string()));
            assert_eq!(cmd.args.len(), 2);
        } else {
            panic!("Expected Command node");
        }
    }

    #[test]
    fn test_parse_command_with_series() {
        let mut parser = Parser::new("ma:20@close");
        let result = parser.parse().unwrap();
        if let ExpressionNode::Command(cmd) = result {
            assert_eq!(cmd.name, "ma");
            assert_eq!(cmd.series.len(), 1);
        } else {
            panic!("Expected Command node");
        }
    }

    #[test]
    fn test_parse_expression() {
        let mut parser = Parser::new("close > ma:20");
        let result = parser.parse().unwrap();
        if let ExpressionNode::Binary { operator, .. } = result {
            assert_eq!(operator.name, ">");
        } else {
            panic!("Expected Binary expression");
        }
    }
}
