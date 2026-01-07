//! Types for directive AST

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3::IntoPyObject;

use super::tokenizer::Loc;

/// A primitive value (number, string, or boolean)
#[derive(Debug, Clone)]
pub enum Primitive {
    Int(i64),
    Float(f64),
    String(String),
    Bool(bool),
}

impl Primitive {
    pub fn to_python(&self, py: Python<'_>) -> PyResult<PyObject> {
        match self {
            Primitive::Int(i) => Ok(i.into_pyobject(py)?.into_any().unbind()),
            Primitive::Float(f) => Ok(f.into_pyobject(py)?.into_any().unbind()),
            Primitive::String(s) => Ok(s.into_pyobject(py)?.into_any().unbind()),
            // Bool returns a Borrowed reference, need to convert to owned
            Primitive::Bool(b) => Ok(b.into_pyobject(py)?.to_owned().into_any().unbind()),
        }
    }
}

impl std::fmt::Display for Primitive {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Primitive::Int(i) => write!(f, "{}", i),
            Primitive::Float(fl) => write!(f, "{}", fl),
            Primitive::String(s) => write!(f, "{}", s),
            Primitive::Bool(b) => write!(f, "{}", b),
        }
    }
}

/// An argument node
#[derive(Debug, Clone)]
pub struct ArgumentNode {
    pub loc: Loc,
    pub value: Option<Primitive>,
}

/// A series argument node (can be a column name or a nested directive)
#[derive(Debug, Clone)]
pub enum SeriesArgumentNode {
    Column(Loc, String),
    Directive(Loc, Box<ExpressionNode>),
    Empty(Loc),
}

/// A scalar node with a value
#[derive(Debug, Clone)]
pub struct ScalarNode<T> {
    pub loc: Loc,
    pub value: T,
}

/// An operator node
#[derive(Debug, Clone)]
pub struct OperatorNode {
    pub loc: Loc,
    pub name: String,
    pub priority: i32,
}

/// A command node
#[derive(Debug, Clone)]
pub struct CommandNode {
    pub loc: Loc,
    pub name: String,
    pub sub: Option<String>,
    pub args: Vec<ArgumentNode>,
    pub series: Vec<SeriesArgumentNode>,
}

impl CommandNode {
    pub fn to_python(&self, py: Python<'_>, commands: &Bound<'_, PyDict>) -> PyResult<PyObject> {
        // Import the Python CommandNode class to create instances
        let stock_pandas = py.import("stock_pandas.directive.node")?;
        let command_node_class = stock_pandas.getattr("CommandNode")?;
        let scalar_node_class = stock_pandas.getattr("ScalarNode")?;
        let argument_node_class = stock_pandas.getattr("ArgumentNode")?;
        let series_argument_node_class = stock_pandas.getattr("SeriesArgumentNode")?;

        // Create the name ScalarNode
        let name_node = scalar_node_class.call1((self.loc, &self.name))?;

        // Create the sub ScalarNode if present
        let sub_node: PyObject = if let Some(ref sub) = self.sub {
            scalar_node_class.call1((self.loc, sub))?.unbind()
        } else {
            py.None()
        };

        // Create argument nodes
        let args_list = PyList::empty(py);
        for arg in &self.args {
            let value: PyObject = if let Some(ref v) = arg.value {
                let scalar = scalar_node_class.call1((arg.loc, v.to_python(py)?))?;
                scalar.unbind()
            } else {
                py.None()
            };
            let arg_node = argument_node_class.call1((arg.loc, value))?;
            args_list.append(arg_node)?;
        }

        // Create series argument nodes
        let series_list = PyList::empty(py);
        for series in &self.series {
            let value: PyObject = match series {
                SeriesArgumentNode::Column(loc, name) => {
                    let scalar = scalar_node_class.call1((*loc, name))?;
                    series_argument_node_class.call1((*loc, scalar))?.unbind()
                }
                SeriesArgumentNode::Directive(loc, expr) => {
                    let directive = expr.to_python(py, commands)?;
                    series_argument_node_class.call1((*loc, directive))?.unbind()
                }
                SeriesArgumentNode::Empty(loc) => {
                    series_argument_node_class.call1((*loc, py.None()))?.unbind()
                }
            };
            series_list.append(value)?;
        }

        // Create the CommandNode
        let node = command_node_class.call1((
            self.loc,
            name_node,
            args_list,
            series_list,
            sub_node,
        ))?;

        // Call create() to get the actual Command object
        let context_module = py.import("stock_pandas.directive.command")?;
        let context_class = context_module.getattr("Context")?;

        let cache_module = py.import("stock_pandas.directive.cache")?;
        let cache_class = cache_module.getattr("DirectiveCache")?;
        let cache = cache_class.call0()?;

        // Get the input string representation
        let input_str = format!("{}", self);
        let context = context_class.call1((input_str, cache, commands))?;

        let result = node.call_method1("create", (context,))?;
        Ok(result.unbind())
    }
}

impl std::fmt::Display for CommandNode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.name)?;
        if let Some(ref sub) = self.sub {
            write!(f, ".{}", sub)?;
        }
        if !self.args.is_empty() {
            write!(f, ":")?;
            let args_str: Vec<String> = self.args.iter()
                .map(|a| a.value.as_ref().map(|v| v.to_string()).unwrap_or_default())
                .collect();
            write!(f, "{}", args_str.join(","))?;
        }
        if !self.series.is_empty() {
            write!(f, "@")?;
            let series_str: Vec<String> = self.series.iter()
                .map(|s| match s {
                    SeriesArgumentNode::Column(_, name) => name.clone(),
                    SeriesArgumentNode::Directive(_, expr) => format!("({})", expr),
                    SeriesArgumentNode::Empty(_) => String::new(),
                })
                .collect();
            write!(f, "{}", series_str.join(","))?;
        }
        Ok(())
    }
}

/// Expression node types
#[derive(Debug, Clone)]
pub enum ExpressionNode {
    /// A scalar value
    Scalar(ScalarNode<Primitive>),
    /// A command
    Command(CommandNode),
    /// A binary expression
    Binary {
        loc: Loc,
        operator: OperatorNode,
        left: Box<ExpressionNode>,
        right: Box<ExpressionNode>,
    },
    /// A unary expression
    Unary {
        loc: Loc,
        operator: OperatorNode,
        expression: Box<ExpressionNode>,
    },
}

impl ExpressionNode {
    pub fn to_python(&self, py: Python<'_>, commands: &Bound<'_, PyDict>) -> PyResult<PyObject> {
        match self {
            ExpressionNode::Scalar(scalar) => {
                scalar.value.to_python(py)
            }
            ExpressionNode::Command(cmd) => {
                cmd.to_python(py, commands)
            }
            ExpressionNode::Binary { loc, operator, left, right } => {
                let node_module = py.import("stock_pandas.directive.node")?;
                let expr_node_class = node_module.getattr("ExpressionNode")?;
                let op_node_class = node_module.getattr("OperatorNode")?;

                let left_py = left.to_python(py, commands)?;
                let right_py = right.to_python(py, commands)?;

                // Get the operator formula from the operator module
                let op_module = py.import("stock_pandas.directive.operator")?;
                let formula = get_operator_formula(py, &op_module, &operator.name)?;

                let op_node = op_node_class.call1((
                    operator.loc,
                    &operator.name,
                    formula,
                    operator.priority,
                ))?;

                let node = expr_node_class.call1((*loc, left_py, op_node, right_py))?;

                // Create context and call create()
                let context = create_context(py, commands, &format!("{}", self))?;
                let result = node.call_method1("create", (context,))?;
                Ok(result.unbind())
            }
            ExpressionNode::Unary { loc, operator, expression } => {
                let node_module = py.import("stock_pandas.directive.node")?;
                let unary_node_class = node_module.getattr("UnaryExpressionNode")?;
                let op_node_class = node_module.getattr("OperatorNode")?;

                let expr_py = expression.to_python(py, commands)?;

                // Get the unary operator formula
                let op_module = py.import("stock_pandas.directive.operator")?;
                let formula = get_unary_operator_formula(py, &op_module, &operator.name)?;

                let op_node = op_node_class.call1((
                    operator.loc,
                    &operator.name,
                    formula,
                    operator.priority,
                ))?;

                let node = unary_node_class.call1((*loc, op_node, expr_py))?;

                // Create context and call create()
                let context = create_context(py, commands, &format!("{}", self))?;
                let result = node.call_method1("create", (context,))?;
                Ok(result.unbind())
            }
        }
    }
}

impl std::fmt::Display for ExpressionNode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ExpressionNode::Scalar(s) => write!(f, "{}", s.value),
            ExpressionNode::Command(c) => write!(f, "{}", c),
            ExpressionNode::Binary { operator, left, right, .. } => {
                write!(f, "{}{}{}", left, operator.name, right)
            }
            ExpressionNode::Unary { operator, expression, .. } => {
                write!(f, "{}{}", operator.name, expression)
            }
        }
    }
}

fn get_operator_formula(_py: Python<'_>, op_module: &Bound<'_, pyo3::types::PyModule>, name: &str) -> PyResult<PyObject> {
    // Map operator names to their formula functions
    let operators = [
        ("MULTIPLICATION_OPERATORS", &["*", "/"][..]),
        ("ADDITION_OPERATORS", &["+", "-"][..]),
        ("STYLE_OPERATORS", &["//", "\\", "><"][..]),
        ("EQUALITY_OPERATORS", &["==", "!="][..]),
        ("RELATIONAL_OPERATORS", &["<", "<=", ">=", ">"][..]),
        ("BITWISE_AND_OPERATORS", &["&"][..]),
        ("BITWISE_XOR_OPERATORS", &["^"][..]),
        ("BITWISE_OR_OPERATORS", &["|"][..]),
    ];

    for (dict_name, ops) in operators {
        if ops.contains(&name) {
            let dict = op_module.getattr(dict_name)?;
            // Use try to handle the potential KeyError
            match dict.call_method1("get", (name,)) {
                Ok(entry) => {
                    if !entry.is_none() {
                        // Entry is (formula, priority) tuple
                        let formula = entry.get_item(0)?;
                        return Ok(formula.unbind());
                    }
                }
                Err(_) => continue,
            }
        }
    }

    Err(pyo3::exceptions::PyValueError::new_err(format!(
        "Unknown operator: {}",
        name
    )))
}

fn get_unary_operator_formula(_py: Python<'_>, op_module: &Bound<'_, pyo3::types::PyModule>, name: &str) -> PyResult<PyObject> {
    let dict = op_module.getattr("UNARY_OPERATORS")?;
    match dict.call_method1("get", (name,)) {
        Ok(entry) => {
            if !entry.is_none() {
                let formula = entry.get_item(0)?;
                return Ok(formula.unbind());
            }
        }
        Err(_) => {}
    }

    Err(pyo3::exceptions::PyValueError::new_err(format!(
        "Unknown unary operator: {}",
        name
    )))
}

fn create_context(py: Python<'_>, commands: &Bound<'_, PyDict>, input: &str) -> PyResult<PyObject> {
    let context_module = py.import("stock_pandas.directive.command")?;
    let context_class = context_module.getattr("Context")?;

    let cache_module = py.import("stock_pandas.directive.cache")?;
    let cache_class = cache_module.getattr("DirectiveCache")?;
    let cache = cache_class.call0()?;

    let context = context_class.call1((input, cache, commands))?;
    Ok(context.unbind())
}
