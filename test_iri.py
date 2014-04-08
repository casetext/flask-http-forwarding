import unittest

from libcasetext.iri import IRI

class TestIRI(unittest.TestCase):
    def test_valid_iri_parts(self):
        """ Passing in valid IRI parts should parse correctly. """
        test_iri = IRI(country="us",
                       classification="judgment",
                       authority="us",
                       date="2013-01-01",
                       identifier="hello",
                       language="eng",
                       revision="published",
                       renderer="test",
                       render_date="2013-05-08",
                       format_code="xml")
        self.assertEqual(test_iri.work_str(), "/us/judgment/us/2013-01-01/hello/main")
        self.assertEqual(test_iri.expression_str(), "/us/judgment/us/2013-01-01/hello/eng@published#test/2013-05-08/main")
        self.assertEqual(test_iri.manifestation_str(), "/us/judgment/us/2013-01-01/hello/eng@published#test/2013-05-08/main.xml")

    def test_valid_work_iri(self):
        """ A valid work IRI should parse correctly. """
        test_iri = IRI("/us/judgment/us/2013-01-01/06-575/main")
        self.assertEqual(test_iri.work_str(), "/us/judgment/us/2013-01-01/06-575/main")
        self.assertEqual(test_iri.country_code, "us")
        self.assertEqual(test_iri.classification, "judgment")
        self.assertEqual(test_iri.authority, "us")
        self.assertEqual(test_iri.date.year, 2013)
        self.assertEqual(test_iri.date.month, 1)
        self.assertEqual(test_iri.date.day, 1)
        self.assertEqual(test_iri.identifier, "06-575")
        self.assertEqual(test_iri.path, "main")

    def test_valid_expression_iri(self):
        """ A valid expression IRI should parse correctly. """
        test_iri = IRI("/us/judgment/us/2013-01-01/06-575/eng@published/part1/section6")
        self.assertEqual(test_iri.work_str(), "/us/judgment/us/2013-01-01/06-575/part1/section6")
        self.assertEqual(test_iri.expression_str(), "/us/judgment/us/2013-01-01/06-575/eng@published/part1/section6")
        self.assertEqual(test_iri.country_code, "us")
        self.assertEqual(test_iri.classification, "judgment")
        self.assertEqual(test_iri.authority, "us")
        self.assertEqual(test_iri.date.year, 2013)
        self.assertEqual(test_iri.date.month, 1)
        self.assertEqual(test_iri.date.day, 1)
        self.assertEqual(test_iri.identifier, "06-575")
        self.assertEqual(test_iri.language, "eng")
        self.assertEqual(test_iri.revision, "published")
        self.assertEqual(test_iri.path, "part1/section6")

    def test_valid_expression_optional_iri(self):
        """ A valid expression IRI with optional part should parse correctly. """
        test_iri = IRI("/us/judgment/us/2013-01-01/06-575/eng@published#mayer/2014-06-07/part1/section6")
        self.assertEqual(test_iri.work_str(), "/us/judgment/us/2013-01-01/06-575/part1/section6")
        self.assertEqual(test_iri.expression_str(), "/us/judgment/us/2013-01-01/06-575/eng@published#mayer/2014-06-07/part1/section6")
        self.assertEqual(test_iri.country_code, "us")
        self.assertEqual(test_iri.classification, "judgment")
        self.assertEqual(test_iri.authority, "us")
        self.assertEqual(test_iri.date.year, 2013)
        self.assertEqual(test_iri.date.month, 1)
        self.assertEqual(test_iri.date.day, 1)
        self.assertEqual(test_iri.identifier, "06-575")
        self.assertEqual(test_iri.language, "eng")
        self.assertEqual(test_iri.revision, "published")
        self.assertEqual(test_iri.renderer, "mayer")
        self.assertEqual(test_iri.render_date.year, 2014)
        self.assertEqual(test_iri.render_date.month, 6)
        self.assertEqual(test_iri.render_date.day, 7)
        self.assertEqual(test_iri.path, "part1/section6")

    def test_valid_manifestation_iri(self):
        """ A valid manifestation IRI should parse correctly. """
        test_iri = IRI("/us/judgment/us/2013-01-01/06-575/eng@published#mayer/2014-06-07/part1/section6")
        self.assertEqual(test_iri.work_str(), "/us/judgment/us/2013-01-01/06-575/part1/section6")
        self.assertEqual(test_iri.expression_str(), "/us/judgment/us/2013-01-01/06-575/eng@published#mayer/2014-06-07/part1/section6")
        self.assertEqual(test_iri.country_code, "us")
        self.assertEqual(test_iri.classification, "judgment")
        self.assertEqual(test_iri.authority, "us")
        self.assertEqual(test_iri.date.year, 2013)
        self.assertEqual(test_iri.date.month, 1)
        self.assertEqual(test_iri.date.day, 1)
        self.assertEqual(test_iri.identifier, "06-575")
        self.assertEqual(test_iri.language, "eng")
        self.assertEqual(test_iri.revision, "published")
        self.assertEqual(test_iri.renderer, "mayer")
        self.assertEqual(test_iri.render_date.year, 2014)
        self.assertEqual(test_iri.render_date.month, 6)
        self.assertEqual(test_iri.render_date.day, 7)
        self.assertEqual(test_iri.path, "part1/section6")

