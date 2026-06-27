// Node smoke test for the *browser* engine-load path.
// It loads Pyodide from the copied public/pyodide/ assets (the exact files the
// browser serves), unpacks public/engine.tgz, imports src.fortis, loads the
// same helper as src/lib/engine.js, and runs a real derivation.
import { readFileSync } from "fs";
import { pathToFileURL } from "url";
import { resolve } from "path";

const log = (...a) => console.log(...a);

try {
  // Load Pyodide from the served assets, not the bare npm entry point.
  const pyUrl = pathToFileURL(resolve("public/pyodide/pyodide.mjs")).href;
  const { loadPyodide } = await import(pyUrl);
  const py = await loadPyodide({ indexURL: resolve("public/pyodide") + "/" });
  log("1. pyodide loaded from public/pyodide/");

  const tgz = readFileSync("public/engine.tgz");
  py.unpackArchive(new Uint8Array(tgz), "gztar", { extractDir: "/work" });
  log("2. unpacked:", py.runPython(`import os; sorted(os.listdir("/work"))`).toString());

  py.runPython(`import sys; sys.path.insert(0, "/work")`);
  py.runPython(`import src.fortis`);
  log("3. imported src.fortis");

  // Load the production helper, then call run_derivations() like the app does.
  const HELPER = readFileSync("src/lib/engine.js", "utf8")
    .split("const HELPER = `")[1]
    .split("`;")[0]
    .replace(/\\\\/g, "\\"); // un-escape the JS template-string backslashes
  py.runPython(HELPER);
  const json = py.runPython("run_derivations()");
  const data = JSON.parse(json);
  if (data.error) throw new Error("engine returned error: " + JSON.stringify(data.error));
  const first = data.derivations[0];
  log(`4. run_derivations(): ${data.derivations.length} word(s)`);
  log(`   ${first.ipa}  ->  ${first.surface}  (${first.steps.length} steps)`);
  log("SMOKE TEST PASSED");
} catch (e) {
  const m = (e && e.message) ? e.message : String(e);
  console.log("FAILED:\n" + m.split("\n").slice(-25).join("\n"));
  process.exit(1);
}
