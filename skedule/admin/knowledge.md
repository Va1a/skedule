# Admin Blueprint Knowledge

## Purpose
Provides administrative tools for schedule management and configuration.

## Key Features
- Schedule creation/deletion by week
- Shift template management
- Individual shift configuration
- Employee assignment management

## Routes
- /schedule/configure: Weekly schedule configuration
- /schedule/configure/templates: Template management
- /schedule/configure/add-shift: New shift creation
- /schedule/configure/shift/<id>: Shift editing

## Templates
Templates store reusable shift patterns with:
- Name and timing
- Employee constraints
- Default employee assignments