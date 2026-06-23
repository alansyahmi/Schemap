# Database Schema Context

This document contains a token-optimized representation of the database schema for LLM context injection.


Table: users


Columns:

- id (INTEGER): Primary key
- name (TEXT): 


Relationships:
```text
users
 └─ orders
```



Table: orders


Columns:

- id (INTEGER): Primary key
- user_id (INTEGER): 






Common User Journeys:

Users → Orders

