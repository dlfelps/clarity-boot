Feature: Detailed Complexity Attribution Metrics
  As an engineering lead,
  I want the complexity report to provide specific, quantifiable metrics,
  so that I can make data-driven decisions about my project's architecture and technical debt.

  Background:
    Given the Clarity Engine has successfully generated a transparency report for a project

  Scenario: Viewing the feature-level complexity summary
    When I view the "Complexity Analysis" section of the report
    Then I should see a summary table with a row for each Feature defined in the Gherkin specs
    And each row in the summary table should contain columns for:
      | Metric                        |
      | Total Scenarios               |
      | Total Code Footprint (LOC)    |
      | Overall Cyclomatic Complexity |
      | Component Dependencies        |

  Scenario: Drilling down into the scenario-level complexity
    Given I am viewing the feature-level complexity summary
    When I select the "Post Management" feature to view its detailed breakdown
    Then I should see a detailed table with a row for each Scenario within that feature
    And each row in the detailed table should contain columns for:
      | Metric                   |
      | Code Footprint (LOC)     |
      | Cyclomatic Complexity    |
      | Unique Code Contribution |

  Scenario: Identifying a complexity hotspot
    Given the detailed breakdown for the "Post Management" feature is visible
    And the "User can format post with custom CSS" scenario has a "Cyclomatic Complexity" of "28"
    And other scenarios in the same feature have a complexity of less than "10"
    Then the report should visually flag the "User can format post with custom CSS" scenario as a "Complexity Hotspot"
