/*
to read user files: https://web.dev/read-files/
 */
const output = document.getElementById("output");

const editor = CodeMirror.fromTextArea(document.getElementById("code"), {
    mode: {
        name: "python",
        version: 3,
        singleLineStringErrors: false
    },
    lineNumbers: true,
    indentUnit: 4,
    matchBrackets: true
});

output.value = "Initializing...\n";

async function loadCode() {
    // for archives: https://pyodide.org/en/stable/usage/loading-custom-python-code.html#from-javascript
    let response = await fetch("base.py");
    return response.text();
}

async function main() {
    let baseCode = await loadCode();
    editor.setValue(baseCode);

    let pyodide = await loadPyodide();
    await pyodide.loadPackage("numpy");
    await pyodide.loadPackage("pyyaml");
    // await pyodide.loadPackage("micropip");
    // const micropip = pyodide.pyimport("micropip");

    // Pyodide ready
    output.value += "Ready!\n";
    evaluatePython();
    return pyodide;
}

let pyodideReadyPromise = main();

function setOutput(s) {
    output.value = ">>>" + s + "\n";
}

async function evaluatePython() {
    let pyodide = await pyodideReadyPromise;
    try {
        console.log(editor.getValue())
        let output = await pyodide.runPythonAsync(editor.getValue());
        setOutput(output);
    } catch (err) {
        setOutput(err);
    }
}
