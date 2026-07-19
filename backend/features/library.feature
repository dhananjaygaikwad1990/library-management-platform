Feature: Complete library management workflows
  The service must protect library data and support catalog, inventory,
  member, borrowing, return, availability, overdue, and fine workflows.

  Scenario: Create, list, search, and filter catalog records
    Given an author named "Jane Austen" exists
    And a book titled "Pride and Prejudice" with ISBN "ISBN-001" exists for that author
    And a book titled "Emma" with ISBN "ISBN-002" exists for that author
    When I search books for "Pride"
    Then 1 book is returned with title "Pride and Prejudice"
    And filtering books by the author returns 2 books
    And the author list contains "Jane Austen"

  Scenario: Track total and available physical copies
    Given a book titled "Dune" with ISBN "ISBN-010" exists
    And the book has a copy "DUNE-A" with status "available"
    And the book has a copy "DUNE-B" with status "maintenance"
    When I request book availability
    Then "Dune" has 2 total copies and 1 available copy
    And availability search for "Dun" returns 1 book

  Scenario: Search members by name and member ID
    Given a member named "Emma Woodhouse" with email "emma@test.local" exists
    And a member named "George Knightley" with email "george@test.local" exists
    When I search members for "Wood"
    Then 1 member is returned with email "emma@test.local"
    When I search members using the saved member ID
    Then 1 member is returned with email "emma@test.local"

  Scenario: Automatically link a logged-in borrower to a member
    Given a book titled "Persuasion" with ISBN "ISBN-020" exists
    And the book has a copy "PER-A" with status "available"
    When "new.reader@test.local" borrows the book for 14 days
    Then a member record exists for "new.reader@test.local"
    And the selected copy status is "borrowed"
    And that member has 1 loan with status "on loan"

  Scenario: Reject an invalid due date
    Given a book titled "Northanger Abbey" with ISBN "ISBN-021" exists
    And the book has a copy "NOR-A" with status "available"
    When I try to borrow with a due date before the borrow date
    Then the operation fails with "Due date cannot be before the borrow date"

  Scenario: Reject borrowing when no copy is available
    Given a book titled "Mansfield Park" with ISBN "ISBN-022" exists
    And the book has a copy "MAN-A" with status "maintenance"
    When I try to borrow the unavailable book
    Then the operation fails with "No available copy found for the requested book"

  Scenario: Calculate overdue days and current fine
    Given an overdue loan for "overdue@test.local" that was due 3 days ago
    When I request borrow history for "overdue@test.local"
    Then the loan status is "overdue"
    And the loan has 3 overdue days and a fine of 3.00

  Scenario: Return a copy, finalize its fine, and clear the fine
    Given an overdue loan for "returner@test.local" that was due 2 days ago
    When "returner@test.local" returns the loan
    Then the selected copy status is "available"
    And the returned loan has a fine of 2.00
    When "returner@test.local" clears the loan fine
    Then the returned loan has a fine of 0.00

  Scenario: Prevent one member from returning another member's loan
    Given an active loan for "owner@test.local"
    When "other@test.local" tries to return the loan
    Then the operation fails with "Borrow record"

  Scenario: Authenticate and enforce role authorization through HTTP
    Given I am logged in through HTTP as "visitor@example.com" with password "VisitorPass1!"
    When I try to create an author through HTTP
    Then the HTTP response status is 403
    When I request books through HTTP without a token
    Then the HTTP response status is 401

  Scenario: Borrow and return through the authenticated HTTP API
    Given a book titled "The Test Book" with ISBN "ISBN-030" exists
    And the book has a copy "TEST-A" with status "available"
    And I am logged in through HTTP as "student@example.com" with password "StudentPass1!"
    When I borrow the saved book through HTTP
    Then the HTTP response status is 200
    And my HTTP borrow history contains 1 loan
    When I return that loan through HTTP
    Then the HTTP response status is 200
    And the selected copy status is "available"

  Scenario: Report database conflicts and missing records
    Given an author named "Duplicate Author" exists
    And a book titled "Unique Book" with ISBN "ISBN-040" exists for that author
    When I try to create another book with ISBN "ISBN-040"
    Then the operation fails with "Database integrity error"
    When I request a missing book
    Then the operation fails with "not found"
