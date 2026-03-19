# 08_REASONING_RUNTIME_EXECUTION_SPEC

Version: 3.0
Status: Required

## Purpose

Define the execution behavior of the RTW after governance gates pass.

## Runtime Execution Responsibilities

- accept input after routing
- maintain execution context
- call gate engine before output emission
- enforce correction or halt on violations
- emit validated outputs only

## Build-Time Analogue

The Main Builder Agent uses an analogous execution loop:
- read next requirement
- decide direct execution or delegation
- issue bounded contract if delegating
- validate return
- merge or reject
- continue until acceptance criteria are met

## Return-to-Main-Agent Rule

All delegated work must re-enter the main execution loop before becoming accepted build content.

## Invalid Behaviors

- sub-agent direct publish
- sub-agent direct merge
- hidden retries without updated status
- untracked modification of accepted files
