import importlib.util
import json
from pathlib import Path
import re
import tempfile
import shutil
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/walletfreak'
PROVIDERS = json.loads((ROOT / 'providers.json').read_text())
EXPECTED = {'marriott','hilton','hyatt','ihg','accor','wyndham','choice','best-western','american','delta','united','southwest','jetblue','alaska-hawaiian','air-canada','british-airways','iberia','air-france-klm','lufthansa-group','emirates','qatar','singapore','ana','jal','cathay-pacific','qantas','turkish','capital-one-travel','amex-travel','chase-travel','citi-travel'}

class Packages(unittest.TestCase):
    def test_unified_coverage_and_catalogs(self):
        self.assertEqual({p['id'] for p in PROVIDERS}, EXPECTED)
        self.assertEqual(len(PROVIDERS), 31)
        self.assertEqual(json.loads((PLUGIN/'providers.json').read_text()), PROVIDERS)
        for path in (ROOT/'.agents/plugins/marketplace.json', ROOT/'.claude-plugin/marketplace.json'):
            catalog=json.loads(path.read_text())
            self.assertEqual(catalog['name'],'walletfreak')
            self.assertEqual([p['name'] for p in catalog['plugins']],['walletfreak','walletfreak-spending'])
        self.assertEqual(sorted(p.name for p in (ROOT/'plugins').iterdir()),['walletfreak','walletfreak-spending'])
        for host in ('codex','claude'):
            m=json.loads((PLUGIN/f'.{host}-plugin/plugin.json').read_text())
            self.assertEqual(m['name'],'walletfreak')
            self.assertEqual(m['version'].split('+')[0],'0.3.0')
        ledger=json.loads((ROOT/'docs/provider-verification.json').read_text())
        self.assertEqual({r['id'] for r in ledger},EXPECTED)
        for p in PROVIDERS:
            self.assertEqual(p['plugin'],'walletfreak')
            self.assertEqual(p['skill'],'provider-research')
            self.assertTrue((PLUGIN/p['guide']).is_file())
            self.assertTrue(p['legacySkill'])
            evidence=next(r for r in ledger if r['id']==p['id'])
            self.assertEqual(p['verification'],evidence['stage'])
            guide=(PLUGIN/p['guide']).read_text()
            self.assertIn(p['programs'][0],guide)
            self.assertIn('https://',guide)

    def test_one_browser_and_portable_package(self):
        self.assertEqual(list((ROOT/'plugins').rglob('.mcp.json')),[PLUGIN/'.mcp.json'])
        config=json.loads((PLUGIN/'.mcp.json').read_text())['mcpServers']
        self.assertEqual(list(config),['walletfreak-browser'])
        self.assertEqual(config['walletfreak-browser']['command'],'python3')
        self.assertEqual(config['walletfreak-browser']['args'][0], '-c')
        self.assertEqual(config['walletfreak-browser']['args'][-1], '${CLAUDE_PLUGIN_ROOT}/scripts/browser.py')
        self.assertEqual(config['walletfreak-browser']['cwd'], '.')
        with tempfile.TemporaryDirectory() as temporary:
            isolated=Path(temporary)/'walletfreak'
            shutil.copytree(PLUGIN,isolated)
            names={s.parent.name for s in isolated.glob('skills/*/SKILL.md')}
            self.assertEqual(names,{'travel-plan','provider-research','traveler-profile','card-travel-benefits','lounge-access','trip-board','walletfreak-setup','wallet-optimizer'})
            for path in isolated.rglob('*.md'):
                for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
                    if target.startswith('https://'):
                        continue
                    resolved=(path.parent/target.split('#')[0]).resolve()
                    self.assertTrue(resolved.is_relative_to(isolated.resolve()),(path,target))
                    self.assertTrue(resolved.is_file(),(path,target))
            self.assertFalse(any(p.is_symlink() for p in isolated.rglob('*')))

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
