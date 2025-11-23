"""
TrendRadar MCP Server - FastMCP 2.0 Implementation

Production-grade MCP tool server implemented with FastMCP 2.0.
Supports both stdio and HTTP transport modes.
"""

import json
from typing import List, Optional, Dict

from fastmcp import FastMCP

from .tools.data_query import DataQueryTools
from .tools.analytics import AnalyticsTools
from .tools.search_tools import SearchTools
from .tools.config_mgmt import ConfigManagementTools
from .tools.system import SystemManagementTools


# Create FastMCP 2.0 application
mcp = FastMCP('trendradar-news')

# Global tool instances (initialized on first request)
_tools_instances = {}


def _get_tools(project_root: Optional[str] = None):
    """Get or create tool instances (singleton pattern)"""
    if not _tools_instances:
        _tools_instances['data'] = DataQueryTools(project_root)
        _tools_instances['analytics'] = AnalyticsTools(project_root)
        _tools_instances['search'] = SearchTools(project_root)
        _tools_instances['config'] = ConfigManagementTools(project_root)
        _tools_instances['system'] = SystemManagementTools(project_root)
    return _tools_instances


# ==================== Data Query Tools ====================

@mcp.tool
async def get_latest_news(
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Get the latest batch of crawled news data to quickly understand current hot topics

    Args:
        platforms: List of platform IDs, e.g., ['zhihu', 'weibo', 'douyin']
                   - When not specified: Uses all platforms configured in config.yaml
                   - Supported platforms come from platforms configuration in config/config.yaml
                   - Each platform has a corresponding name field (e.g., "Zhihu", "Weibo") for easy AI identification
        limit: Return count limit, default 50, maximum 1000
               Note: Actual returned count may be less than requested value, depending on total available news
        include_url: Whether to include URL links, default False (saves tokens)

    Returns:
        JSON formatted news list

    **Important: Data Display Recommendations**
    This tool returns a complete news list (typically 50 items) to you. Please note:
    - **Tool returns**: Complete 50 items ✅
    - **Recommended display**: Show all data to users unless they explicitly request a summary
    - **User expectations**: Users may need complete data, so be cautious with summarization

    **When to summarize**:
    - User explicitly says "give me a summary" or "show me the highlights"
    - When data exceeds 100 items, you can show partial data first and ask if they want to see all

    **Note**: If users ask "why only partial data is shown", they need complete data
    """
    tools = _get_tools()
    result = tools['data'].get_latest_news(platforms=platforms, limit=limit, include_url=include_url)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_trending_topics(
    top_n: int = 10,
    mode: str = 'current'
) -> str:
    """
    Get frequency statistics of personal attention words in news (based on config/frequency_words.txt)

    Note: This tool does not automatically extract news hotspots, but rather counts the frequency
    of your personal attention words (set in config/frequency_words.txt) appearing in news.
    You can customize this attention word list.

    Args:
        top_n: Return TOP N attention words, default 10
        mode: Mode selection
            - daily: Daily cumulative data statistics
            - current: Latest batch data statistics (default)

    Returns:
        JSON formatted list of attention word frequency statistics
    """
    tools = _get_tools()
    result = tools['data'].get_trending_topics(top_n=top_n, mode=mode)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_news_by_date(
    date_query: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Get news data for a specified date, used for historical data analysis and comparison

    Args:
        date_query: Date query, optional formats:
            - Natural language: "today", "yesterday", "day before yesterday", "3 days ago"
            - Standard date: "2024-01-15", "2024/01/15"
            - Default: "today" (saves tokens)
        platforms: List of platform IDs, e.g., ['zhihu', 'weibo', 'douyin']
                   - When not specified: Uses all platforms configured in config.yaml
                   - Supported platforms come from platforms configuration in config/config.yaml
                   - Each platform has a corresponding name field (e.g., "Zhihu", "Weibo") for easy AI identification
        limit: Return count limit, default 50, maximum 1000
               Note: Actual returned count may be less than requested value, depending on total news for the specified date
        include_url: Whether to include URL links, default False (saves tokens)

    Returns:
        JSON formatted news list, containing title, platform, ranking and other information

    **Important: Data Display Recommendations**
    This tool returns a complete news list (typically 50 items) to you. Please note:
    - **Tool returns**: Complete 50 items ✅
    - **Recommended display**: Show all data to users unless they explicitly request a summary
    - **User expectations**: Users may need complete data, so be cautious with summarization

    **When to summarize**:
    - User explicitly says "give me a summary" or "show me the highlights"
    - When data exceeds 100 items, you can show partial data first and ask if they want to see all

    **Note**: If users ask "why only partial data is shown", they need complete data
    """
    tools = _get_tools()
    result = tools['data'].get_news_by_date(
        date_query=date_query,
        platforms=platforms,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)



# ==================== Advanced Data Analysis Tools ====================

@mcp.tool
async def analyze_topic_trend(
    topic: str,
    analysis_type: str = "trend",
    date_range: Optional[Dict[str, str]] = None,
    granularity: str = "day",
    threshold: float = 3.0,
    time_window: int = 24,
    lookahead_hours: int = 6,
    confidence_threshold: float = 0.7
) -> str:
    """
    Unified topic trend analysis tool - integrates multiple trend analysis modes

    Args:
        topic: Topic keyword (required)
        analysis_type: Analysis type, optional values:
            - "trend": Popularity trend analysis (tracks changes in topic popularity)
            - "lifecycle": Lifecycle analysis (complete cycle from appearance to disappearance)
            - "viral": Anomaly popularity detection (identifies suddenly trending topics)
            - "predict": Topic prediction (predicts future potential hot topics)
        date_range: Date range (for trend and lifecycle modes), optional
                    - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} (must be standard date format)
                    - **Description**: AI must automatically calculate and fill specific dates based on current date, cannot use natural language like "today"
                    - **Calculation examples**:
                      - User says "last 7 days" → AI calculates: {"start": "2025-11-11", "end": "2025-11-17"} (assuming today is 11-17)
                      - User says "last week" → AI calculates: {"start": "2025-11-11", "end": "2025-11-17"} (last Monday to last Sunday)
                      - User says "this month" → AI calculates: {"start": "2025-11-01", "end": "2025-11-17"} (November 1st to today)
                    - **Default**: When not specified, defaults to analyzing the last 7 days
        granularity: Time granularity (for trend mode), default "day" (only supports day because underlying data is aggregated by day)
        threshold: Popularity surge multiple threshold (for viral mode), default 3.0
        time_window: Detection time window in hours (for viral mode), default 24
        lookahead_hours: Prediction future hours (for predict mode), default 6
        confidence_threshold: Confidence threshold (for predict mode), default 0.7

    Returns:
        JSON formatted trend analysis results

    **AI Usage Instructions:**
    When users use relative time expressions (like "last 7 days", "past week", "last month"),
    AI must calculate specific YYYY-MM-DD format dates based on current date (obtained from environment <env>).

    **Important**: date_range does not accept natural language like "today", "yesterday", must be YYYY-MM-DD format!

    Examples (assuming today is 2025-11-17):
        - User: "Analyze AI trends for the last 7 days"
          → analyze_topic_trend(topic="artificial intelligence", analysis_type="trend", date_range={"start": "2025-11-11", "end": "2025-11-17"})
        - User: "Check Tesla's popularity this month"
          → analyze_topic_trend(topic="Tesla", analysis_type="lifecycle", date_range={"start": "2025-11-01", "end": "2025-11-17"})
        - analyze_topic_trend(topic="Bitcoin", analysis_type="viral", threshold=3.0)
        - analyze_topic_trend(topic="ChatGPT", analysis_type="predict", lookahead_hours=6)
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_topic_trend_unified(
        topic=topic,
        analysis_type=analysis_type,
        date_range=date_range,
        granularity=granularity,
        threshold=threshold,
        time_window=time_window,
        lookahead_hours=lookahead_hours,
        confidence_threshold=confidence_threshold
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def analyze_data_insights(
    insight_type: str = "platform_compare",
    topic: Optional[str] = None,
    date_range: Optional[Dict[str, str]] = None,
    min_frequency: int = 3,
    top_n: int = 20
) -> str:
    """
    Unified data insights analysis tool - integrates multiple data analysis modes

    Args:
        insight_type: Insight type, optional values:
            - "platform_compare": Platform comparison analysis (compare topic attention across different platforms)
            - "platform_activity": Platform activity statistics (statistics of publishing frequency and active times for each platform)
            - "keyword_cooccur": Keyword co-occurrence analysis (analyze patterns where keywords appear together)
        topic: Topic keyword (optional, applicable for platform_compare mode)
        date_range: **[Object Type]** Date range (optional)
                    - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **Example**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Important**: Must be object format, cannot pass integers
        min_frequency: Minimum co-occurrence frequency (for keyword_cooccur mode), default 3
        top_n: Return TOP N results (for keyword_cooccur mode), default 20

    Returns:
        JSON formatted data insights analysis results

    Examples:
        - analyze_data_insights(insight_type="platform_compare", topic="artificial intelligence")
        - analyze_data_insights(insight_type="platform_activity", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        - analyze_data_insights(insight_type="keyword_cooccur", min_frequency=5, top_n=15)
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_data_insights_unified(
        insight_type=insight_type,
        topic=topic,
        date_range=date_range,
        min_frequency=min_frequency,
        top_n=top_n
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def analyze_sentiment(
    topic: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    date_range: Optional[Dict[str, str]] = None,
    limit: int = 50,
    sort_by_weight: bool = True,
    include_url: bool = False
) -> str:
    """
    Analyze sentiment trends and popularity of news

    Args:
        topic: Topic keyword (optional)
        platforms: List of platform IDs, e.g., ['zhihu', 'weibo', 'douyin']
                   - When not specified: Uses all platforms configured in config.yaml
                   - Supported platforms come from platforms configuration in config/config.yaml
                   - Each platform has a corresponding name field (e.g., "Zhihu", "Weibo") for easy AI identification
        date_range: **[Object Type]** Date range (optional)
                    - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **Example**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Important**: Must be object format, cannot pass integers
        limit: Return news count, default 50, maximum 100
               Note: This tool deduplicates news titles (same title across different platforms kept only once),
               therefore actual returned count may be less than requested limit value
        sort_by_weight: Whether to sort by popularity weight, default True
        include_url: Whether to include URL links, default False (saves tokens)

    Returns:
        JSON formatted analysis results, containing sentiment distribution, popularity trends and related news

    **Important: Data Display Strategy**
    - This tool returns complete analysis results and news list
    - **Default display**: Show complete analysis results (including all news)
    - Filter only when users explicitly request "summary" or "highlights"
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_sentiment(
        topic=topic,
        platforms=platforms,
        date_range=date_range,
        limit=limit,
        sort_by_weight=sort_by_weight,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def find_similar_news(
    reference_title: str,
    threshold: float = 0.6,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Find news similar to the specified news title

    Args:
        reference_title: News title (complete or partial)
        threshold: Similarity threshold, between 0-1, default 0.6
                   Note: Higher threshold means stricter matching and fewer results
        limit: Return count limit, default 50, maximum 100
               Note: Actual returned count depends on similarity matching results, may be less than requested value
        include_url: Whether to include URL links, default False (saves tokens)

    Returns:
        JSON formatted similar news list, containing similarity scores

    **Important: Data Display Strategy**
    - This tool returns complete similar news list
    - **Default display**: Show all returned news (including similarity scores)
    - Filter only when users explicitly request "summary" or "highlights"
    """
    tools = _get_tools()
    result = tools['analytics'].find_similar_news(
        reference_title=reference_title,
        threshold=threshold,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def generate_summary_report(
    report_type: str = "daily",
    date_range: Optional[Dict[str, str]] = None
) -> str:
    """
    Daily/Weekly summary generator - automatically generates hot topic summary reports

    Args:
        report_type: Report type (daily/weekly)
        date_range: **[Object Type]** Custom date range (optional)
                    - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **Example**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Important**: Must be object format, cannot pass integers

    Returns:
        JSON formatted summary report, containing Markdown formatted content
    """
    tools = _get_tools()
    result = tools['analytics'].generate_summary_report(
        report_type=report_type,
        date_range=date_range
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Intelligent Search Tools ====================

@mcp.tool
async def search_news(
    query: str,
    search_mode: str = "keyword",
    date_range: Optional[Dict[str, str]] = None,
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    sort_by: str = "relevance",
    threshold: float = 0.6,
    include_url: bool = False
) -> str:
    """
    Unified search interface, supports multiple search modes

    Args:
        query: Search keyword or content fragment
        search_mode: Search mode, optional values:
            - "keyword": Exact keyword matching (default, suitable for searching specific topics)
            - "fuzzy": Fuzzy content matching (suitable for searching content fragments, filters results with similarity below threshold)
            - "entity": Entity name search (suitable for searching people/places/organizations)
        date_range: Date range (optional)
                    - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **Example**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Description**: AI needs to automatically calculate date range based on user's natural language (like "last 7 days")
                    - **Default**: When not specified, defaults to searching today's news
                    - **Note**: start and end can be the same (indicates single day query)
        platforms: List of platform IDs, e.g., ['zhihu', 'weibo', 'douyin']
                   - When not specified: Uses all platforms configured in config.yaml
                   - Supported platforms come from platforms configuration in config/config.yaml
                   - Each platform has a corresponding name field (e.g., "Zhihu", "Weibo") for easy AI identification
        limit: Return count limit, default 50, maximum 1000
               Note: Actual returned count depends on search matching results (especially in fuzzy mode filters low similarity results)
        sort_by: Sort method, optional values:
            - "relevance": Sort by relevance (default)
            - "weight": Sort by news weight
            - "date": Sort by date
        threshold: Similarity threshold (only valid for fuzzy mode), between 0-1, default 0.6
                   Note: Higher threshold means stricter matching and fewer results
        include_url: Whether to include URL links, default False (saves tokens)

    Returns:
        JSON formatted search results, containing title, platform, ranking and other information

    **Important: Data Display Strategy**
    - This tool returns complete search results list
    - **Default display**: Show all returned news, no summarization or filtering needed
    - Filter only when users explicitly request "summary" or "highlights"

    **AI Usage Instructions:**
    When users use relative time expressions (like "last 7 days", "past week", "last half month"),
    AI must calculate specific YYYY-MM-DD format dates based on current date (obtained from environment <env>).

    **Important**: date_range does not accept natural language like "today", "yesterday", must be YYYY-MM-DD format!

    **Calculation rules** (assuming today from <env> is 2025-11-17):
    - "today" → Don't pass date_range (defaults to today)
    - "last 7 days" → {"start": "2025-11-11", "end": "2025-11-17"}
    - "past week" → {"start": "2025-11-11", "end": "2025-11-17"}
    - "last week" → Calculate last Monday to last Sunday, e.g., {"start": "2025-11-11", "end": "2025-11-17"}
    - "this month" → {"start": "2025-11-01", "end": "2025-11-17"}
    - "last 30 days" → {"start": "2025-10-19", "end": "2025-11-17"}


    Examples (assuming today is 2025-11-17):
        - User: "Today's AI news" → search_news(query="artificial intelligence")
        - User: "AI news for the last 7 days" → search_news(query="artificial intelligence", date_range={"start": "2025-11-11", "end": "2025-11-17"})
        - Specific date: search_news(query="artificial intelligence", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        - Fuzzy search: search_news(query="Tesla price cut", search_mode="fuzzy", threshold=0.4)
    """
    tools = _get_tools()
    result = tools['search'].search_news_unified(
        query=query,
        search_mode=search_mode,
        date_range=date_range,
        platforms=platforms,
        limit=limit,
        sort_by=sort_by,
        threshold=threshold,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def search_related_news_history(
    reference_text: str,
    time_preset: str = "yesterday",
    threshold: float = 0.4,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Search for related news in historical data based on seed news

    Args:
        reference_text: Reference news title (complete or partial)
        time_preset: Time range preset value, optional:
            - "yesterday": Yesterday
            - "last_week": Last week (7 days)
            - "last_month": Last month (30 days)
            - "custom": Custom date range (requires start_date and end_date)
        threshold: Relevance threshold, between 0-1, default 0.4
                   Note: Comprehensive similarity calculation (70% keyword overlap + 30% text similarity)
                   Higher threshold means stricter matching and fewer results
        limit: Return count limit, default 50, maximum 100
               Note: Actual returned count depends on relevance matching results, may be less than requested value
        include_url: Whether to include URL links, default False (saves tokens)

    Returns:
        JSON formatted related news list, containing relevance scores and time distribution

    **Important: Data Display Strategy**
    - This tool returns complete related news list
    - **Default display**: Show all returned news (including relevance scores)
    - Filter only when users explicitly request "summary" or "highlights"
    """
    tools = _get_tools()
    result = tools['search'].search_related_news_history(
        reference_text=reference_text,
        time_preset=time_preset,
        threshold=threshold,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Configuration & System Management Tools ====================

@mcp.tool
async def get_current_config(
    section: str = "all"
) -> str:
    """
    Get current system configuration

    Args:
        section: Configuration section, optional values:
            - "all": All configurations (default)
            - "crawler": Crawler configuration
            - "push": Push configuration
            - "keywords": Keywords configuration
            - "weights": Weights configuration

    Returns:
        JSON formatted configuration information
    """
    tools = _get_tools()
    result = tools['config'].get_current_config(section=section)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_system_status() -> str:
    """
    Get system running status and health check information

    Returns system version, data statistics, cache status and other information

    Returns:
        JSON formatted system status information
    """
    tools = _get_tools()
    result = tools['system'].get_system_status()
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def trigger_crawl(
    platforms: Optional[List[str]] = None,
    save_to_local: bool = False,
    include_url: bool = False
) -> str:
    """
    Manually trigger a crawl task (optional persistence)

    Args:
        platforms: Specify platform ID list, e.g., ['zhihu', 'weibo', 'douyin']
                   - When not specified: Uses all platforms configured in config.yaml
                   - Supported platforms come from platforms configuration in config/config.yaml
                   - Each platform has a corresponding name field (e.g., "Zhihu", "Weibo") for easy AI identification
                   - Note: Failed platforms will be listed in the failed_platforms field of the returned result
        save_to_local: Whether to save to local output directory, default False
        include_url: Whether to include URL links, default False (saves tokens)

    Returns:
        JSON formatted task status information, containing:
        - platforms: List of successfully crawled platforms
        - failed_platforms: List of failed platforms (if any)
        - total_news: Total number of crawled news
        - data: News data

    Examples:
        - Temporary crawl: trigger_crawl(platforms=['zhihu'])
        - Crawl and save: trigger_crawl(platforms=['weibo'], save_to_local=True)
        - Use default platforms: trigger_crawl()  # Crawl all platforms configured in config.yaml
    """
    tools = _get_tools()
    result = tools['system'].trigger_crawl(platforms=platforms, save_to_local=save_to_local, include_url=include_url)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Startup Entry Point ====================

def run_server(
    project_root: Optional[str] = None,
    transport: str = 'stdio',
    host: str = '0.0.0.0',
    port: int = 3333
):
    """
    Start MCP server

    Args:
        project_root: Project root directory path
        transport: Transport mode, 'stdio' or 'http'
        host: HTTP mode listening address, default 0.0.0.0
        port: HTTP mode listening port, default 3333
    """
    # Initialize tool instances
    _get_tools(project_root)

    # Print startup information
    print()
    print("=" * 60)
    print("  TrendRadar MCP Server - FastMCP 2.0")
    print("=" * 60)
    print(f"  Transport Mode: {transport.upper()}")

    if transport == 'stdio':
        print("  Protocol: MCP over stdio (standard input/output)")
        print("  Description: Communicate with MCP clients through standard input/output")
    elif transport == 'http':
        print(f"  Listen Address: http://{host}:{port}")
        print(f"  HTTP Endpoint: http://{host}:{port}/mcp")
        print("  Protocol: MCP over HTTP (production environment)")

    if project_root:
        print(f"  Project Directory: {project_root}")
    else:
        print("  Project Directory: Current directory")

    print()
    print("  Registered Tools:")
    print("    === Basic Data Query (P0 Core) ===")
    print("    1. get_latest_news        - Get latest news")
    print("    2. get_news_by_date       - Query news by date (supports natural language)")
    print("    3. get_trending_topics    - Get trending topics")
    print()
    print("    === Intelligent Search Tools ===")
    print("    4. search_news                  - Unified news search (keyword/fuzzy/entity)")
    print("    5. search_related_news_history  - Historical related news search")
    print()
    print("    === Advanced Data Analysis ===")
    print("    6. analyze_topic_trend      - Unified topic trend analysis (popularity/lifecycle/viral/prediction)")
    print("    7. analyze_data_insights    - Unified data insights analysis (platform comparison/activity/keyword co-occurrence)")
    print("    8. analyze_sentiment        - Sentiment trend analysis")
    print("    9. find_similar_news        - Similar news search")
    print("    10. generate_summary_report - Daily/weekly summary generation")
    print()
    print("    === Configuration & System Management ===")
    print("    11. get_current_config      - Get current system configuration")
    print("    12. get_system_status       - Get system running status")
    print("    13. trigger_crawl           - Manually trigger crawl task")
    print("=" * 60)
    print()

    # Run server based on transport mode
    if transport == 'stdio':
        mcp.run(transport='stdio')
    elif transport == 'http':
        # HTTP mode (production recommended)
        mcp.run(
            transport='http',
            host=host,
            port=port,
            path='/mcp'  # HTTP endpoint path
        )
    else:
        raise ValueError(f"Unsupported transport mode: {transport}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='TrendRadar MCP Server - News Hot Topics Aggregation MCP Tool Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
For detailed configuration tutorial, see: README-Cherry-Studio.md
        """
    )
    parser.add_argument(
        '--transport',
        choices=['stdio', 'http'],
        default='stdio',
        help='Transport mode: stdio (default) or http (production environment)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='HTTP mode listening address, default 0.0.0.0'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=3333,
        help='HTTP mode listening port, default 3333'
    )
    parser.add_argument(
        '--project-root',
        help='Project root directory path'
    )

    args = parser.parse_args()

    run_server(
        project_root=args.project_root,
        transport=args.transport,
        host=args.host,
        port=args.port
    )
