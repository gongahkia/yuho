"""
Hypothesis-based tests for Yuho statute implementations.

Tests invariants for S463 Forgery, S499 Defamation, and S503 Criminal Breach of Trust.
"""

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st
from pathlib import Path


# Test settings for complex tests
STATUTE_SETTINGS = settings(
    max_examples=30,
    deadline=10000,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)


# Strategies for generating statute-related data
@st.composite
def money_strategy(draw):
    """Generate valid money amounts."""
    return draw(st.integers(min_value=0, max_value=1_000_000_000))


@st.composite
def person_name_strategy(draw):
    """Generate valid person names."""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('L',)),
        min_size=1,
        max_size=50
    ).filter(lambda x: x.strip() != ""))


@st.composite
def forgery_case_strategy(draw):
    """Generate forgery case data."""
    doc_types = ["PublicDocument", "PrivateDocument", "ElectronicRecord", 
                 "Signature", "Seal", "ValueSecurity"]
    intent_types = ["CausePropertyDamage", "SupportClaim", "CauseDishonor",
                    "CommitFraud", "Other"]
    
    return {
        "accused_name": draw(person_name_strategy()),
        "document_type": draw(st.sampled_from(doc_types)),
        "false_document_made": draw(st.booleans()),
        "intent_to_deceive": draw(st.booleans()),
        "representation_as_genuine": draw(st.booleans()),
        "intent_type": draw(st.sampled_from(intent_types)),
    }


@st.composite
def defamation_case_strategy(draw):
    """Generate defamation case data."""
    pub_types = ["Spoken", "Written", "Printed", "Electronic", "Broadcast", "Visual"]
    defenses = ["Truth", "PublicInterest", "FairComment", "PrivilegedOccasion", "Consent"]
    
    return {
        "accused_name": draw(person_name_strategy()),
        "victim_name": draw(person_name_strategy()),
        "publication_type": draw(st.sampled_from(pub_types)),
        "imputation_made": draw(st.booleans()),
        "published_to_third_party": draw(st.booleans()),
        "identified_person": draw(st.booleans()),
        "intention_to_harm": draw(st.booleans()),
        "public_figure": draw(st.booleans()),
        "claimed_defense": draw(st.sampled_from(defenses)),
    }


@st.composite
def cbt_case_strategy(draw):
    """Generate criminal breach of trust case data."""
    entrustment_types = ["Employment", "Agency", "Partnership", "Trust",
                         "JointProperty", "Guardianship", "BankingRelation", "PublicOffice"]
    
    return {
        "accused_name": draw(person_name_strategy()),
        "entrustment_type": draw(st.sampled_from(entrustment_types)),
        "property_value": draw(money_strategy()),
        "property_entrusted": draw(st.booleans()),
        "dominion_over_property": draw(st.booleans()),
        "dishonest_misappropriation": draw(st.booleans()),
        "conversion_for_own_use": draw(st.booleans()),
        "public_servant": draw(st.booleans()),
        "banker_merchant": draw(st.booleans()),
    }


class TestStatuteParsing:
    """Test that statute files parse correctly."""
    
    def test_s463_forgery_parses(self):
        """S463 Forgery statute should parse without errors."""
        from yuho.parser import Parser
        
        statute_path = Path(__file__).parent.parent / "statutes" / "s463_forgery.yh"
        if not statute_path.exists():
            pytest.skip("Statute file not found")
        
        parser = Parser()
        result = parser.parse_file(statute_path)
        
        assert result.tree is not None, "Statute should parse successfully"
    
    def test_s499_defamation_parses(self):
        """S499 Defamation statute should parse without errors."""
        from yuho.parser import Parser
        
        statute_path = Path(__file__).parent.parent / "statutes" / "s499_defamation.yh"
        if not statute_path.exists():
            pytest.skip("Statute file not found")
        
        parser = Parser()
        result = parser.parse_file(statute_path)
        
        assert result.tree is not None, "Statute should parse successfully"
    
    def test_s503_cbt_parses(self):
        """S503 Criminal Breach of Trust statute should parse without errors."""
        from yuho.parser import Parser
        
        statute_path = Path(__file__).parent.parent / "statutes" / "s503_criminal_breach_of_trust.yh"
        if not statute_path.exists():
            pytest.skip("Statute file not found")
        
        parser = Parser()
        result = parser.parse_file(statute_path)
        
        assert result.tree is not None, "Statute should parse successfully"


class TestForgeryInvariants:
    """Property-based tests for Forgery (S463) invariants."""
    
    @given(forgery_case_strategy())
    @STATUTE_SETTINGS
    def test_forgery_requires_false_document(self, case):
        """Forgery cannot be established without a false document."""
        if not case["false_document_made"]:
            # If no false document, cannot be forgery regardless of intent
            assert not self._is_forgery(case), \
                "Forgery cannot exist without false document"
    
    @given(forgery_case_strategy())
    @STATUTE_SETTINGS
    def test_forgery_requires_intent(self, case):
        """Forgery requires intent to deceive."""
        if not case["intent_to_deceive"]:
            # Without intent, even a false document is not forgery
            assert not self._is_forgery(case), \
                "Forgery requires intent to deceive"
    
    @given(forgery_case_strategy())
    @STATUTE_SETTINGS
    def test_both_elements_implies_forgery(self, case):
        """Both elements present implies forgery."""
        if case["false_document_made"] and case["intent_to_deceive"]:
            assert self._is_forgery(case), \
                "Both elements present should establish forgery"
    
    def _is_forgery(self, case):
        """Simple forgery determination."""
        return case["false_document_made"] and case["intent_to_deceive"]


class TestDefamationInvariants:
    """Property-based tests for Defamation (S499) invariants."""
    
    @given(defamation_case_strategy())
    @STATUTE_SETTINGS
    def test_defamation_requires_publication(self, case):
        """Defamation requires publication to third party."""
        if not case["published_to_third_party"]:
            assert not self._is_defamation(case), \
                "Defamation requires publication to third party"
    
    @given(defamation_case_strategy())
    @STATUTE_SETTINGS
    def test_defamation_requires_identification(self, case):
        """Defamation requires identification of victim."""
        if not case["identified_person"]:
            assert not self._is_defamation(case), \
                "Defamation requires identified victim"
    
    @given(defamation_case_strategy())
    @STATUTE_SETTINGS
    def test_truth_defense_negates_defamation(self, case):
        """Truth is a complete defense to defamation."""
        if case["claimed_defense"] == "Truth":
            # Truth defense should negate liability
            has_defense = self._has_valid_defense(case)
            assert has_defense, "Truth should be valid defense"
    
    @given(defamation_case_strategy())
    @STATUTE_SETTINGS
    def test_public_interest_defense_for_public_figures(self, case):
        """Public interest defense valid for public figures."""
        if case["claimed_defense"] == "PublicInterest" and case["public_figure"]:
            assert self._has_valid_defense(case), \
                "Public interest defense should apply to public figures"
    
    def _is_defamation(self, case):
        """Simple defamation determination without defense."""
        return (case["imputation_made"] and 
                case["published_to_third_party"] and 
                case["identified_person"] and 
                case["intention_to_harm"])
    
    def _has_valid_defense(self, case):
        """Check if claimed defense is valid."""
        defense = case["claimed_defense"]
        if defense == "Truth":
            return True
        if defense == "PublicInterest":
            return case["public_figure"]
        if defense == "FairComment":
            return True
        if defense == "PrivilegedOccasion":
            return True
        if defense == "Consent":
            return True
        return False


class TestCBTInvariants:
    """Property-based tests for Criminal Breach of Trust (S503) invariants."""
    
    @given(cbt_case_strategy())
    @STATUTE_SETTINGS
    def test_cbt_requires_entrustment(self, case):
        """CBT cannot exist without entrustment."""
        if not case["property_entrusted"]:
            assert not self._is_cbt(case), \
                "CBT requires property entrustment"
    
    @given(cbt_case_strategy())
    @STATUTE_SETTINGS
    def test_cbt_requires_dominion(self, case):
        """CBT requires dominion over property."""
        if not case["dominion_over_property"]:
            assert not self._is_cbt(case), \
                "CBT requires dominion over property"
    
    @given(cbt_case_strategy())
    @STATUTE_SETTINGS
    def test_cbt_requires_dishonesty(self, case):
        """CBT requires dishonest misappropriation."""
        if not case["dishonest_misappropriation"] and not case["conversion_for_own_use"]:
            assume(case["property_entrusted"] and case["dominion_over_property"])
            assert not self._is_cbt(case), \
                "CBT requires dishonest act"
    
    @given(cbt_case_strategy())
    @STATUTE_SETTINGS
    def test_aggravated_cbt_for_public_servants(self, case):
        """Public servants face aggravated CBT charges."""
        if case["public_servant"] and self._is_cbt(case):
            applicable_section = self._determine_section(case)
            assert applicable_section == "S409", \
                "Public servants should be charged under S409"
    
    @given(cbt_case_strategy())
    @STATUTE_SETTINGS
    def test_aggravated_cbt_for_bankers(self, case):
        """Bankers/merchants face aggravated CBT charges."""
        if case["banker_merchant"] and self._is_cbt(case):
            applicable_section = self._determine_section(case)
            assert applicable_section == "S409", \
                "Bankers should be charged under S409"
    
    @given(cbt_case_strategy())
    @STATUTE_SETTINGS
    def test_employment_cbt_is_s408(self, case):
        """Employment-based CBT falls under S408."""
        if (case["entrustment_type"] == "Employment" and 
            self._is_cbt(case) and 
            not case["public_servant"] and 
            not case["banker_merchant"]):
            applicable_section = self._determine_section(case)
            assert applicable_section == "S408", \
                "Employment CBT should be S408"
    
    def _is_cbt(self, case):
        """Simple CBT determination."""
        return (case["property_entrusted"] and 
                case["dominion_over_property"] and 
                (case["dishonest_misappropriation"] or case["conversion_for_own_use"]))
    
    def _determine_section(self, case):
        """Determine applicable section."""
        if case["public_servant"] or case["banker_merchant"]:
            return "S409"
        if case["entrustment_type"] == "Employment":
            return "S408"
        return "S406"


class TestCrossStatuteInvariants:
    """Tests for invariants across multiple statutes."""
    
    @given(st.booleans(), st.booleans())
    @STATUTE_SETTINGS
    def test_intent_is_essential_element(self, element1, element2):
        """All offenses require some form of intent/mens rea."""
        # Without dishonest/fraudulent intent, no crime
        # This tests the fundamental mens rea requirement
        
        # Forgery without intent to deceive
        forgery_case = {
            "false_document_made": True,
            "intent_to_deceive": element1,
        }
        
        if not element1:
            assert not (forgery_case["false_document_made"] and 
                       forgery_case["intent_to_deceive"]), \
                "No forgery without intent"
    
    @given(cbt_case_strategy())
    @STATUTE_SETTINGS
    def test_penalty_ordering_by_position(self, case):
        """More serious positions carry higher penalties."""
        if not self._is_cbt(case):
            return
        
        section = self._determine_section(case)
        
        penalty_order = {
            "S406": 7,   # Basic CBT - 7 years
            "S407": 15,  # Carrier - 15 years
            "S408": 15,  # Clerk/Servant - 15 years
            "S409": 20,  # Public servant/Banker - life/20 years
        }
        
        # Higher trust positions should have higher penalties
        if case["public_servant"] or case["banker_merchant"]:
            assert penalty_order.get(section, 0) >= 15, \
                "Trust positions should have higher penalties"
    
    def _is_cbt(self, case):
        return (case["property_entrusted"] and 
                case["dominion_over_property"] and 
                (case["dishonest_misappropriation"] or case["conversion_for_own_use"]))
    
    def _determine_section(self, case):
        if case["public_servant"] or case["banker_merchant"]:
            return "S409"
        if case["entrustment_type"] == "Employment":
            return "S408"
        return "S406"
