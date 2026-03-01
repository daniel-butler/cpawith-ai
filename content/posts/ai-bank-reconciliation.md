---
title: "I Asked AI to Automate My Bank Reconciliation. Here's What It Got Right — and What Almost Blew Up."
slug: ai-bank-reconciliation
date: 2026-03-01
description: "A former CPA and Amazon engineer walks through using AI to build bank reconciliation automation — the prompts, the validation, and the subtle mistakes only an accountant would catch."
tags: [reconciliation, AI, automation, month-end-close]
draft: true
---

If you're an accountant, you already know this number: **20 to 50 hours per month.** That's how long the average finance team spends on cash reconciliation alone, across 3 to 5 systems, mostly in Excel. You download a CSV from the bank. You download another from your GL. You paste them side by side and start matching. VLOOKUP if you're efficient. Eyeballing if you're honest.

I did this for six years. Then I became a software engineer. Now I lead AI adoption across engineering teams at Amazon. And I wanted to know: what happens when you ask an AI to build the thing that would have saved me all those hours?

Here's exactly what happened.

## The setup

I started with two files that any accountant would recognize:

- **Bank export:** 347 transactions from a Chase business checking account. One month. CSV with date, description, amount, and running balance.
- **GL export:** 312 transactions from QuickBooks Online. Same period. Date, memo, debit, credit, account.

The gap between 347 and 312 is already telling you something. Bank fees, pending transactions, timing differences — the usual suspects.

## The prompt

I didn't write code. I described the process:

> I have two CSV files: a bank statement export and a general ledger export from QuickBooks. I need to reconcile them. Match transactions by amount and date (within a 3-day window for timing differences). Flag anything that appears in one file but not the other. Group the unmatched items by likely reason: bank fees, pending transactions, and true discrepancies. Output a summary showing the reconciled balance, total matched, and a list of exceptions.

That's it. No Python. No pandas. No technical jargon. Just a clear description of the process — the same way you'd describe it in a process memo or a SOX narrative.

## What the AI produced

In about 30 seconds, the AI generated a working script. Without getting into the code, here's what it did:

1. **Loaded both CSVs** and normalized the columns (date formats, amount signs, stripping whitespace from descriptions)
2. **Matched transactions** by amount first, then filtered by date proximity (±3 days)
3. **Categorized unmatched items** into bank fees (descriptions containing "fee," "service charge," "monthly maintenance"), pending transactions (in bank but not GL), and true discrepancies
4. **Generated a summary report** with totals and an exception list

On the first run, it matched **289 of 312 GL transactions** to bank transactions. That's a 92.6% match rate. The remaining 23 GL items and 58 bank items went into the exception buckets.

I ran the whole thing in under a minute. The same process used to take me a full day.

## Where it got things right

**Amount matching was solid.** When a bank transaction and a GL entry had the exact same dollar amount within the date window, it found the match. This is the boring, mechanical part of reconciliation that eats most of your time — and it's exactly what automation should handle.

**Fee detection worked.** It correctly identified 11 bank fees that hadn't been recorded in the GL yet. These are the transactions you'd normally catch during the recon and post as adjusting entries. The AI flagged them cleanly.

**The output was readable.** The summary report looked like something I'd actually hand to a reviewer. Matched count, unmatched count, net difference, exception list with descriptions. Not a wall of data — a structured report.

## Where it almost blew up

Here's where it gets interesting. And this is the part that no Python tutorial will teach you.

### 1. The date cutoff problem

The AI matched a $47,200 wire transfer that posted at the bank on March 1st to a GL entry dated February 28th. Looked like a clean match — same amount, within the 3-day window.

**The problem:** That wire was for a different transaction entirely. The February 28th GL entry was an outgoing payment to a vendor. The March 1st bank entry was an incoming wire from a customer. Same amount, pure coincidence. The AI matched them because the numbers lined up.

A developer would look at the match rate and move on. An accountant would look at the direction — one's a debit, one's a credit — and catch it immediately.

**The fix:** I updated the prompt to specify that matches must have the same sign (both positive or both negative), not just the same absolute amount. Thirty seconds to describe. The AI fixed the code in ten.

### 2. The duplicate payment trap

Two payments to the same vendor, both for $3,150.00, five days apart. The AI matched the first bank transaction to the first GL entry — correct. But then it matched the second bank transaction to the *same* GL entry, because the first match wasn't being excluded from the pool.

This is a classic reconciliation error that junior accountants make too. Once a transaction is matched, it's consumed. You don't get to use it twice.

**The fix:** I told the AI that each transaction can only be matched once — first come, first served. Again, this is something you'd specify in a process memo. You just have to know to say it.

### 3. The rounding ghost

Fourteen transactions were off by $0.01. The bank rounded differently than QuickBooks on sales tax calculations. The AI flagged all fourteen as discrepancies.

Technically correct. Practically useless. Any accountant knows a penny variance on a sales tax calculation is immaterial. But the AI doesn't know your materiality threshold unless you tell it.

**The fix:** I added a tolerance parameter — match transactions within $0.05. The fourteen penny variances disappeared. The real discrepancies stood out.

## What this tells you

The AI didn't replace my accounting knowledge. It **amplified** it. Here's the pattern:

- **The repeatable process** (load files, match by amount and date, categorize exceptions) — the AI built this in 30 seconds. This is the part that used to take a full day.
- **The judgment calls** (which matches are real, what's material, where the risk is) — that's still you. That's your training. That's your value.

Every mistake the AI made was a mistake I've seen humans make too. The difference is that when I caught it and described the fix, the AI updated the logic instantly. A junior accountant takes three close cycles to internalize the same lesson.

## The result

After three rounds of prompting and validation — about 20 minutes of work total — I had a reconciliation process that:

- Matches transactions accurately (including direction and one-to-one constraints)
- Handles penny variances with a materiality threshold
- Categorizes exceptions by type
- Produces a reviewer-ready report
- Runs in under 10 seconds on a month's worth of data

**20 minutes of describing and validating, instead of 8 hours of matching.** And next month, it runs again in 10 seconds with zero additional work.

## What you need to try this

You don't need to learn Python. You need to:

1. **Know your process cold.** If you can describe it in a process memo, you can describe it to an AI.
2. **Know where the risk is.** The AI doesn't know your materiality threshold, your cutoff procedures, or your vendor payment patterns. You do.
3. **Be willing to iterate.** The first output won't be perfect. Neither was your first month-end close. The difference is that fixing the AI's mistakes takes minutes, not months.

The hard part isn't the technology. The hard part is the same thing it's always been — knowing what "right" looks like. And you already know that.

---

*Questions about trying this with your own reconciliation? [Reach out](mailto:daniel@cpawith.ai) — I read everything.*
