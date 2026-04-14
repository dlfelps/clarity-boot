Feature: Transparency Report Generation
  As a software developer or engineering lead,
  I want to generate a detailed transparency report for a completed project,
  so that I can understand the complexity, cost, and health of my implementation.

  Background:
    Given I have a completed software project that includes:
      | File Type                 | Path                                   |
      | An approved Gherkin spec  | my_project/specs/calculator.feature    |
      | The application code      | my_project/src/app.py                  |
      | The passing test suite    | my_project/features/steps/steps.py     |

  Scenario: Generating a full report for a valid project
    When I instruct the Clarity Engine to generate a transparency report for "my_project"
    Then the engine should execute the project's test suite while measuring code coverage
    And the engine should perform a static analysis of the application code
    And the engine should generate a multi-tabbed report dashboard
    And the report should contain a "Complexity Analysis" section with metrics for each feature and scenario

  Scenario: Handling a project with failing tests
    Given a project where the test suite fails to pass
    When I attempt to generate a transparency report
    Then the engine should halt the process
    And the engine should show an error message: "Cannot generate a report for a project with failing tests."

  Scenario: Handling a project with missing files
    Given a project that is missing the specs directory
    When I attempt to generate a transparency report
    Then the engine should halt the process
    And the engine should show an error message: "Project is missing a 'specs/' directory with approved feature files."

  Scenario: Generating a report covering multiple feature specs
    Given I have a completed project with multiple approved specs
    When I instruct the Clarity Engine to generate a transparency report for "multi_project"
    Then the report should contain metrics for all features across all specs
