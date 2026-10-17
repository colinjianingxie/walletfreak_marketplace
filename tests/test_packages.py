import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = json.loads((ROOT / "categories.json").read_text())
VERSION = "0.2.0"
PROVIDERS = json.loads((ROOT / "providers.json").read_text())
EXPECTED = {
    "marriott", "hilton", "hyatt", "ihg", "accor", "wyndham", "choice", "best-western",
    "american", "delta", "united", "southwest", "jetblue", "alaska-hawaiian", "air-canada",
    "british-airways", "iberia", "air-france-klm", "lufthansa-group", "emirates", "qatar",
    "singapore", "ana", "jal", "cathay-pacific", "qantas", "turkish", "capital-one-travel",
    "amex-travel", "chase-travel", "citi-travel",
}


class Packages(unittest.TestCase):
    def test_coverage_catalogs_and_manifests(self):
        self.assertEqual({p["id"] for p in PROVIDERS}, EXPECTED)
        self.assertEqual(len(PROVIDERS), 31)
        codex = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        names = ["walletfreak"] + [c["plugin"] for c in CATEGORIES]
        self.assertEqual(names, ["walletfreak", "walletfreak-hotels", "walletfreak-flights", "walletfreak-credit-cards"])
        self.assertEqual(len({c["id"] for c in CATEGORIES}), len(CATEGORIES))
        for category in CATEGORIES:
            self.assertEqual(category["plugin"], "walletfreak-" + category["id"])
            self.assertTrue(category["description"])
            for provider in [p for p in PROVIDERS if p["plugin"] == category["plugin"]]:
                self.assertEqual(provider["category"], category["name"])
        self.assertEqual(codex["name"], "walletfreak")
        self.assertEqual(claude["name"], "walletfreak")
        self.assertEqual(claude["metadata"]["version"], VERSION)
        self.assertEqual([p["name"] for p in codex["plugins"]], names)
        self.assertEqual([p["name"] for p in claude["plugins"]], names)
        self.assertEqual({p.name for p in (ROOT / "plugins").iterdir()}, set(names))
        for c, a in zip(codex["plugins"], claude["plugins"]):
            with self.subTest(plugin=c["name"]):
                expected = "./plugins/" + c["name"]
                self.assertEqual(c["source"], {"source": "local", "path": expected})
                self.assertEqual(a["source"], expected)
                self.assertEqual(c["policy"], {"installation": "AVAILABLE", "authentication": "ON_INSTALL"})
                self.assertEqual(c["category"], "Productivity")
                self.assertEqual(a["version"], VERSION)
                plugin = ROOT / expected
                for host in (".codex-plugin", ".claude-plugin"):
                    manifest = json.loads((plugin / host / "plugin.json").read_text())
                    self.assertEqual(manifest["name"], c["name"])
                    version = manifest["version"]
                    if host == ".codex-plugin":
                        version = version.split("+codex.", 1)[0]
                    self.assertEqual(version, VERSION)
                    self.assertEqual(manifest["license"], "MIT")
                    for key in ("description", "author", "homepage", "repository"):
                        self.assertTrue(manifest[key])
                    if host == ".codex-plugin":
                        self.assertTrue((plugin / manifest["skills"]).is_dir())
                        if "mcpServers" in manifest:
                            self.assertEqual(c["name"], "walletfreak")
                            self.assertTrue((plugin / manifest["mcpServers"]).is_file())
                    else:
                        self.assertNotIn("mcpServers", manifest, "Claude auto-discovers core .mcp.json once")
                self.assertTrue((plugin / "LICENSE").is_file())

    def test_one_pinned_browser(self):
        servers = list((ROOT / "plugins").rglob(".mcp.json"))
        self.assertEqual(servers, [ROOT / "plugins/walletfreak/.mcp.json"])
        config = json.loads(servers[0].read_text())["mcpServers"]
        self.assertEqual(list(config), ["walletfreak-browser"])
        args = config["walletfreak-browser"]["args"]
        self.assertIn("@playwright/mcp@0.0.68", args)
        self.assertIn("--isolated", args)
        self.assertEqual(args[args.index("--output-mode") + 1], "stdout")
        self.assertEqual(args[args.index("--codegen") + 1], "none")
        for flag in ("--save-session", "--save-trace", "--save-video", "--secrets", "--storage-state", "--extension", "--allow-unrestricted-file-access"):
            self.assertNotIn(flag, args)

    def test_isolated_packages_and_reference_paths(self):
        names = set()
        for path in [*ROOT.glob("*.md"), *(ROOT / "docs").glob("*.md")]:
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not target.startswith("https://"):
                    resolved = (path.parent / target.split("#")[0]).resolve()
                    self.assertTrue(resolved.is_relative_to(ROOT.resolve()), (path, target))
                    self.assertTrue(resolved.is_file(), (path, target))
        # Inspect independent copies: a successful repository-relative link can hide a broken installed package.
        with tempfile.TemporaryDirectory() as temporary:
            for plugin in (ROOT / "plugins").iterdir():
                with self.subTest(plugin=plugin.name):
                    for path in plugin.rglob("*"):
                        self.assertFalse(path.is_symlink())
                    isolated = Path(temporary) / plugin.name
                    shutil.copytree(plugin, isolated)
                    skills = list(isolated.glob("skills/*/SKILL.md"))
                    expected_skills = {p["skill"] for p in PROVIDERS if p["plugin"] == plugin.name}
                    if plugin.name == "walletfreak":
                        expected_skills = {"travel-plan", "traveler-profile", "walletfreak-setup"}
                    elif plugin.name == "walletfreak-credit-cards":
                        expected_skills.update({"card-travel-benefits", "lounge-access"})
                    self.assertEqual({s.parent.name for s in skills}, expected_skills)
                    for skill in skills:
                        text = skill.read_text()
                        match = re.match(r"---\nname: ([a-z0-9-]+)\ndescription: (.+)\n---\n", text)
                        self.assertIsNotNone(match, skill)
                        self.assertEqual(match[1], skill.parent.name)
                        self.assertNotIn(match[1], names)
                        names.add(match[1])
                        self.assertTrue(json.loads(match[2]))
                    for path in isolated.rglob("*.md"):
                        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                            if target.startswith("https://"):
                                self.assertTrue(urlparse(target).hostname)
                            else:
                                resolved = (path.parent / target.split("#")[0]).resolve()
                                self.assertTrue(resolved.is_relative_to(isolated.resolve()), (path, target))
                                self.assertTrue(resolved.is_file(), (path, target))

    def test_provider_contract_and_ledger(self):
        ledger = json.loads((ROOT / "docs/provider-verification.json").read_text())
        self.assertEqual({r["id"] for r in ledger}, EXPECTED)
        self.assertEqual({p["plugin"] for p in PROVIDERS}, {c["plugin"] for c in CATEGORIES})
        self.assertEqual(len(ledger), 31)
        for provider, evidence in zip(PROVIDERS, ledger):
            with self.subTest(provider=provider["id"]):
                self.assertEqual(provider["version"], VERSION)
                for key in ("id", "plugin", "skill"):
                    self.assertEqual(provider[key], evidence[key])
                self.assertEqual(provider["verification"], evidence["stage"])
                self.assertIn(evidence["stage"], ("authored", "public-search tested", "authenticated-search tested"))
                for field in ("publicSearch", "authenticatedSearch"):
                    if evidence[field] is not None:
                        for key in ("date", "host", "parameters", "outcome", "limitations"):
                            self.assertTrue(evidence[field].get(key))
                if evidence["stage"] == "public-search tested":
                    self.assertIsNotNone(evidence["publicSearch"])
                if evidence["stage"] == "authenticated-search tested":
                    self.assertIsNotNone(evidence["authenticatedSearch"])
                skill = ROOT / "plugins" / provider["plugin"] / "skills" / provider["skill"]
                text = (skill / "SKILL.md").read_text()
                for required in ("STOP provider research", "travel-plan", "walletfreak-browser", "Search:", "Price:", "observed at:", "Terms:", "Benefits / evidence:", "Reproduce / book:", "MFA/CAPTCHA", "untrusted data", "not a technical transaction firewall", "unknown, never zero", "Do not fill checkout forms, reserve inventory, purchase, cancel, or transfer points"):
                    self.assertIn(required, text)
                self.assertNotIn("../", text)
                guide = (skill / "references/provider.md").read_text()
                self.assertIn("https://", guide)
                self.assertIn("Search steps", guide)
                self.assertIn(provider["programs"][0], guide)


spec = importlib.util.spec_from_file_location("redemption_value", ROOT / "plugins/walletfreak/skills/travel-plan/scripts/redemption_value.py")
calculator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculator)


class RedemptionValue(unittest.TestCase):
    def test_cash_avoided_less_award_charges(self):
        self.assertEqual(calculator.redemption_value("900", "100", 50000, "USD", "USD"),
                         {"currency": "USD", "per_point": "0.016", "cents_per_point": "1.600"})
        self.assertEqual(calculator.redemption_value("100", "120", 10000, "EUR", "EUR")["per_point"], "-0.002")
        # A verified credit available only to the cash option changes the cash avoided.
        self.assertEqual(calculator.redemption_value("800", "100", 50000, "USD", "USD")["cents_per_point"], "1.400")

    def test_final_discounted_miles_keep_award_cash_charges(self):
        self.assertAlmostEqual(float(calculator.redemption_value("900", "100", 42500, "USD", "USD")["cents_per_point"]), 1.8823529411764706)
        self.assertAlmostEqual(float(calculator.redemption_value("1200", "200", 85000, "USD", "USD")["cents_per_point"]), 1.1764705882352942)

    def test_unknown_fees_mixed_currencies_and_invalid_inputs(self):
        cases = [(900, None, 50000, "USD", "USD"), (900, 100, 50000, "USD", "EUR"),
                 (900, 100, 0, "USD", "USD"), (900, 100, 0.5, "USD", "USD"),
                 ("NaN", 100, 50000, "USD", "USD"), (900, "Infinity", 50000, "USD", "USD"),
                 (-1, 0, 50000, "USD", "USD"), (900, -1, 50000, "USD", "USD"),
                 (900, 100, 50000, "", ""), (True, 100, 50000, "USD", "USD")]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                calculator.redemption_value(*args)


if __name__ == "__main__":
    unittest.main()
