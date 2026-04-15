Feature: Comparison Report Generation
  As an engineering lead,
  I want to compare the Phase 2 transparency reports from two different implementations
  of the same specification,
  so that I can understand how architectural choices affect complexity and code footprint.

  Background:
    Given I have access to the Clarity Engine

  Scenario: Comparing two reports with identical feature sets
    Given two Phase 2 report directories exist for the same specification
    When I run clarity compare on the two report directories
    Then a "compare.html" file should be created in the output directory
    And the comparison report should contain both project names
    And the comparison report should contain side-by-side metrics for each feature
    And the comparison report should contain per-scenario delta columns

  Scenario: Rejecting reports with mismatched feature sets
    Given two Phase 2 report directories with different feature sets exist
    When I run clarity compare on the two report directories
    Then the command should fail with an error containing "different feature sets"

  Scenario: Rejecting a report directory without data.json
    Given a report directory that is missing its data.json file
    When I run clarity compare on the missing and a valid report directory
    Then the command should fail with an error containing "No data.json found"
