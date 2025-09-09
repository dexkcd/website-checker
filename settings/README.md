# Settings Configuration

This folder contains configuration files for the University Website Information Collector.

## Files

### `crawl_sections.json`

This file defines the sections and subsections that the scraper will look for when analyzing university websites. The structure is:

```json
{
  "sections": [
    {
      "section_name": "Section Name",
      "section_definition": "Description of what this section covers",
      "subsection": [
        {
          "subsection_name": "Subsection Name",
          "subsection_definition": "Description of what this subsection covers"
        }
      ]
    }
  ]
}
```

### Customization

You can customize the sections by:

1. **Modifying existing sections**: Change the names and definitions
2. **Adding new sections**: Add new section objects to the array
3. **Adding new subsections**: Add new subsection objects to any section
4. **Using placeholders**: Use `[organization name]` and `[city, country]` placeholders that will be replaced with actual values

### Placeholders

- `[organization name]`: Will be replaced with the actual organization name
- `[city, country]`: Will be replaced with the city and country (if detected)

### Example

```json
{
  "section_name": "Working at [organization name]",
  "subsection_name": "Living and working in [city, country]"
}
```

Will become:
- "Working at Stanford University"
- "Living and working in Stanford, California"

## How It Works

1. The scraper crawls the website and collects all pages
2. For each section/subsection, it analyzes the content using keyword matching
3. Pages are scored based on relevance to each subsection
4. The most relevant pages are displayed under each subsection
5. Screenshots are taken of each page for visual reference

## Keywords

The system automatically extracts keywords from section and subsection definitions to find relevant pages. It removes common stop words and focuses on meaningful terms that are likely to appear in relevant content.
