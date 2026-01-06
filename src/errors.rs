//! Error types for stock-pandas-rs

use pyo3::prelude::*;
use pyo3::exceptions::{PyValueError, PySyntaxError};
use thiserror::Error;

/// Errors that can occur during directive parsing
#[derive(Error, Debug)]
pub enum DirectiveError {
    #[error("Syntax error at line {line}, column {column}: {message}")]
    SyntaxError {
        line: usize,
        column: usize,
        message: String,
    },

    #[error("Value error: {0}")]
    ValueError(String),

    #[error("Unknown command: {0}")]
    UnknownCommand(String),

    #[error("Invalid argument: {0}")]
    InvalidArgument(String),
}

impl From<DirectiveError> for PyErr {
    fn from(err: DirectiveError) -> PyErr {
        match err {
            DirectiveError::SyntaxError { .. } => {
                PySyntaxError::new_err(err.to_string())
            }
            DirectiveError::ValueError(msg) => {
                PyValueError::new_err(msg)
            }
            DirectiveError::UnknownCommand(msg) => {
                PyValueError::new_err(format!("unknown command: {}", msg))
            }
            DirectiveError::InvalidArgument(msg) => {
                PyValueError::new_err(msg)
            }
        }
    }
}

/// Errors that can occur during indicator calculation
#[derive(Error, Debug)]
pub enum IndicatorError {
    #[error("Invalid period: {0}")]
    InvalidPeriod(String),

    #[error("Array too short: expected at least {expected} elements, got {got}")]
    ArrayTooShort { expected: usize, got: usize },

    #[error("Invalid argument: {0}")]
    InvalidArgument(String),
}

impl From<IndicatorError> for PyErr {
    fn from(err: IndicatorError) -> PyErr {
        PyValueError::new_err(err.to_string())
    }
}

pub type DirectiveResult<T> = Result<T, DirectiveError>;
pub type IndicatorResult<T> = Result<T, IndicatorError>;

