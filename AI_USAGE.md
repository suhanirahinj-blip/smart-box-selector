# AI Assistance During Development

AI tools were used as development aids during work on the Smart Box Selector project. They provided implementation suggestions and helped with review and debugging; they did not replace developer decisions or review.

## Areas of Assistance

- **Django structure and implementation guidance:** Assistance was used while shaping the Django application, including its models, serializers, views, and API routing.
- **3D box-packing heuristic:** AI helped develop and refine a deterministic greedy packing approach that considers product rotations, box dimensions, weight limits, and placements. The approach is a heuristic and is not guaranteed to find a globally optimal packing.
- **Code review and debugging:** AI helped inspect implementation behavior and reason about issues such as free-space partitioning, placement overlaps, and box-boundary checks. Suggested changes were reviewed and adjusted during development.
- **API integration and serialization:** Assistance was used to connect the recommendation service to the order detail endpoint and shape its response, including converting box and placement data and preserving Decimal precision in JSON output.
- **Automated tests:** AI helped draft focused Django tests for successful and unsuccessful recommendations, rotation, weight limits, cheapest-box selection, and the API response.

## Developer Review and Verification

The developer reviewed the implementation, made manual corrections, and ran the Django checks and automated tests during development. Test results are evidence from those specific runs; this document does not claim that AI independently verified the project or that every possible behavior has been tested. The developer remains responsible for the code and its use.

AI Tools Used: ChatGPT and GitHub Copilot / VS Code AI (use the actual names you used).
Prompts Used: Include representative prompts actually given during development.
Accepted and Modified Outputs: Explain what suggestions you accepted and what you manually changed.
Mistakes or Limitations: Include actual examples, such as the initial float() conversion losing Decimal precision, which you corrected to str().
Verification: Mention python manage.py check, manual API testing, and the six passing automated tests.