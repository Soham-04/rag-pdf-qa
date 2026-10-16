"""Offline tests: python -m unittest discover -s tests -v"""
import unittest
from io import BytesIO
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, DecodedStreamObject, NameObject
from rag import read_pdf


def make_pdf(text=None, password=None):
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    if text:
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(f'BT /F1 12 Tf 20 250 Td ({text}) Tj ET'.encode())
        page[NameObject('/Contents')] = writer._add_object(stream)
    if password:
        writer.encrypt(password)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


class ExtractionTests(unittest.TestCase):
    def test_text_and_page_reference(self):
        pages, skipped = read_pdf(make_pdf('The project uses FAISS.'), 'demo.pdf')
        self.assertIn('FAISS', pages[0]['text'])
        self.assertEqual((pages[0]['source'], pages[0]['page'], skipped), ('demo.pdf', 1, 0))

    def test_blank_pdf(self):
        with self.assertRaisesRegex(ValueError, 'OCR'):
            read_pdf(make_pdf(), 'scan.pdf')

    def test_encrypted_pdf(self):
        with self.assertRaisesRegex(ValueError, 'Password'):
            read_pdf(make_pdf('Private', 'test'), 'locked.pdf')

    def test_invalid_pdf(self):
        with self.assertRaises(Exception):
            read_pdf(b'not a pdf', 'broken.pdf')

if __name__ == '__main__':
    unittest.main()
