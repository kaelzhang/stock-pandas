//! Directive cache implementation

use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::RwLock;

/// Python-accessible directive cache
#[pyclass]
pub struct PyDirectiveCache {
    store: RwLock<HashMap<String, PyObject>>,
}

#[pymethods]
impl PyDirectiveCache {
    #[new]
    pub fn new() -> Self {
        Self {
            store: RwLock::new(HashMap::new()),
        }
    }

    /// Get a cached directive
    pub fn get(&self, py: Python<'_>, key: &str) -> Option<PyObject> {
        let store = self.store.read().ok()?;
        store.get(key).map(|obj| obj.clone_ref(py))
    }

    /// Set a cached directive
    pub fn set(&self, py: Python<'_>, key: String, value: PyObject) -> PyObject {
        if let Ok(mut store) = self.store.write() {
            store.insert(key, value.clone_ref(py));
        }
        value
    }

    /// Clear the cache
    pub fn clear(&self) {
        if let Ok(mut store) = self.store.write() {
            store.clear();
        }
    }

    /// Get the number of cached directives
    pub fn __len__(&self) -> usize {
        self.store.read().map(|s| s.len()).unwrap_or(0)
    }
}

impl Default for PyDirectiveCache {
    fn default() -> Self {
        Self::new()
    }
}
