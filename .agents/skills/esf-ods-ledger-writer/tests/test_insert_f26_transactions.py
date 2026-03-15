import importlib.util
import re
import sys
import unittest
import zipfile
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "insert_f26_transactions.py"
)
WORKBOOK_PATH = Path(__file__).resolve().parents[4] / "ESF.ods"


def load_module():
    spec = importlib.util.spec_from_file_location("insert_f26_transactions", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class UpdateContentXmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        with zipfile.ZipFile(WORKBOOK_PATH) as workbook:
            cls.original_content = workbook.read("content.xml")

    def test_preserves_formula_namespace_and_openformula_prefix(self):
        transaction = self.module.ParsedTransaction(
            from_value="origem",
            to_value="destino",
            amount_value=self.module.Decimal("1.23"),
            amount_text="1,23",
            type_value="teste",
            date_value="2026-03-15",
            date_text="15/03/26",
            obs_value="linha de teste",
        )

        updated = self.module.update_content_xml(self.original_content, [transaction])
        header = updated[:4000].decode("utf-8")
        formulas = re.findall(r'table:formula="([^"]+)"', updated.decode("utf-8"))

        self.assertIn('xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2"', header)
        self.assertTrue(formulas)
        self.assertTrue(all(formula.startswith("of:=") for formula in formulas))
        self.assertNotIn("=of:", updated.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
