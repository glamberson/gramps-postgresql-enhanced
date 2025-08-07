# Forum Announcements for PostgreSQL Enhanced Addon

## 1. Gramps Discourse Forum
**URL**: https://gramps.discourse.group/
**Category**: Development or Addons
**Title**: [New Addon] PostgreSQL Enhanced - High-Performance Database Backend

### Post:

Hello Gramps Community,

I'm excited to announce the submission of a new experimental addon: **PostgreSQL Enhanced**, a high-performance database backend for Gramps that addresses many limitations of the current database options.

**Pull Request**: https://github.com/gramps-project/addons-source/pull/750

### Why Another PostgreSQL Addon?

While Gramps already has a PostgreSQL addon, this enhanced version was developed to address several critical needs:

- **Modern Technology**: Uses psycopg (v3), not the deprecated psycopg2
- **Performance at Scale**: Successfully tested with 100,000+ person databases
- **Advanced Queries**: Leverages PostgreSQL's full power with JSONB storage
- **Better Architecture**: Connection pooling, proper transaction handling, and dual storage format

### Key Features

**Dual Storage Format**
- Maintains pickle blobs for 100% Gramps compatibility
- Stores JSONB for advanced SQL queries and analysis
- Best of both worlds approach

**Two Database Modes**
- **Monolithic**: All trees in one database with table prefixes (great for organizations)
- **Separate**: Each tree gets its own database (complete isolation)

**Performance Improvements** (vs SQLite)
- 12x faster person lookups (6,135/sec vs 500/sec)
- 100x faster name searches using indexes
- Handles 100,000+ persons effortlessly

### Testing & Reliability

- Extensively tested with real genealogical data
- Successfully imported/managed 86,647 person GEDCOM
- Full compatibility with all Gramps tools verified
- Zero data loss in all test scenarios

### Requirements

- PostgreSQL 15 or higher
- Python 3.9+
- psycopg>=3 (`pip install 'psycopg[binary]'`)

### Current Status

This is version 0.1.0, marked as experimental and targeted at developers and advanced users. While thoroughly tested, I'm looking for community feedback before considering it stable.

### Documentation & Support

- **GitHub Repository**: https://github.com/glamberson/gramps-postgresql-enhanced
- **Installation Guide**: Included in the repository
- **Issue Tracker**: Available on GitHub

### Request for Testers

I'm particularly interested in feedback from:
- Users with large databases (10,000+ persons)
- Organizations managing multiple trees
- Anyone needing better query capabilities
- PostgreSQL database administrators

### Questions?

Feel free to ask questions here or on the GitHub repository. I'm actively maintaining this addon and will respond to issues and feature requests.

Thank you for your consideration, and I look forward to your feedback!

Greg Lamberson
greg@aigenealogyinsights.com

---

## 2. Gramps Users Mailing List
**Email**: gramps-users@lists.sourceforge.net
**Subject**: [ANN] New PostgreSQL Enhanced Addon - Testers Wanted

### Email:

Dear Gramps Users,

I've submitted a new experimental addon called "PostgreSQL Enhanced" that provides a high-performance PostgreSQL database backend for Gramps.

**Why you might be interested:**

If you have:
- Large family trees (10,000+ persons)
- Performance issues with SQLite
- Need for concurrent access
- Interest in advanced queries

This addon might help you.

**Key improvements over existing options:**
- 3-10x faster than SQLite for most operations
- Uses modern psycopg (v3) library
- Tested with 100,000+ person databases
- Two modes: shared database or separate databases per tree

**Status:**
This is experimental (v0.1.0) but has been thoroughly tested. I'm looking for beta testers to provide feedback before marking it stable.

**More Information:**
- Pull Request: https://github.com/gramps-project/addons-source/pull/750
- Documentation: https://github.com/glamberson/gramps-postgresql-enhanced

If you're comfortable with PostgreSQL and want better performance, please give it a try and let me know your experience.

Best regards,
Greg Lamberson

---

## 3. Reddit r/genealogy
**Subreddit**: r/genealogy
**Title**: Developed a high-performance PostgreSQL backend for Gramps - Looking for testers

### Post:

Hi r/genealogy,

For those using Gramps genealogy software with large family trees, I've developed an enhanced PostgreSQL database backend that significantly improves performance.

**The Problem:**
Gramps' default SQLite backend struggles with large databases (20,000+ persons), becoming slow and unresponsive. The existing PostgreSQL addon uses outdated technology and lacks features.

**The Solution:**
PostgreSQL Enhanced addon featuring:
- 12x faster person lookups
- 100x faster searches
- Tested with 100,000+ person databases
- Modern architecture using psycopg v3
- Advanced query capabilities for data analysis

**Who This Helps:**
- Anyone with large family trees
- Professional genealogists
- Family history societies
- Anyone frustrated with Gramps performance

**Current Status:**
Just submitted to Gramps project (PR #750). It's experimental but thoroughly tested. Looking for beta testers before marking stable.

**Links:**
- GitHub: https://github.com/glamberson/gramps-postgresql-enhanced
- PR: https://github.com/gramps-project/addons-source/pull/750

Would love feedback from the community, especially those managing large databases!

---

## 4. Gramps GitHub Discussions
**URL**: https://github.com/gramps-project/gramps/discussions
**Category**: Show and Tell or Ideas
**Title**: PostgreSQL Enhanced Addon - Advanced Database Backend

### Post:

Hi Gramps Developers,

I've just submitted PR #750 to addons-source for a new PostgreSQL Enhanced addon. This addresses several long-standing issues with large database performance in Gramps.

**Technical Highlights:**

```python
# Uses modern psycopg (v3), not psycopg2
# Dual storage: pickle + JSONB
# Connection pooling
# Recursive CTEs for relationship queries
# Full-text search capabilities
```

**Architecture Decisions:**
1. **Dual Storage**: Keeps pickle for compatibility, adds JSONB for queries
2. **Two Modes**: Monolithic (shared DB) or Separate (DB per tree)
3. **No Fallback Policy**: Fails explicitly rather than silently converting data
4. **Data Preservation**: Never auto-deletes PostgreSQL data

**Performance Results:**
- Tested with 86,647 person GEDCOM
- Import rate: ~13 persons/second
- Query performance: millisecond response times
- Memory efficient: Peak 473MB for 86k import

**Future Possibilities:**
With JSONB storage, we could add:
- GraphQL API
- Advanced analytics
- Machine learning features
- Geographic analysis with PostGIS

Looking for code review and suggestions. Happy to discuss design decisions or answer questions about the implementation.

PR: https://github.com/gramps-project/addons-source/pull/750
Repo: https://github.com/glamberson/gramps-postgresql-enhanced

---

## 5. Twitter/X Announcement
**Platform**: Twitter/X
**Character Limit**: 280

### Tweet:

🎉 Just submitted PostgreSQL Enhanced addon for #Gramps #genealogy software!

✅ 12x faster searches
✅ Handles 100k+ persons
✅ Modern psycopg v3
✅ Advanced SQL queries

Perfect for large family trees! 🌳

PR: github.com/gramps-project/addons-source/pull/750
Docs: github.com/glamberson/gramps-postgresql-enhanced

#opensource #postgresql

---

## Posting Schedule Suggestion

1. **Immediately**: Post to Gramps Discourse and GitHub Discussions
2. **Tomorrow**: Post to Gramps Users mailing list
3. **In 2-3 days**: Post to Reddit (after initial feedback)
4. **After PR merge**: Tweet announcement

## Additional Places to Consider

- Gramps Wiki (after merge)
- Personal blog post with detailed benchmarks
- PostgreSQL community forums
- FamilySearch Developers group
- Local genealogy society newsletters