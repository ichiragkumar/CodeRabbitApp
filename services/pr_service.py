import requests
from typing import Dict, Union, List
import os

def fetch_pr_from_github(repo_url: str) -> Dict[str, Union[List, str]]:
    try:
        parts = repo_url.split('/')
        if len(parts) >= 5:
            owner = parts[-2]
            repo = parts[-1]
        else:
            return {"error": "Invalid repository URL format"}
            

        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        

        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if 'GITHUB_TOKEN' in os.environ:
            headers["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"
            

        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            pr_details = response.json()
            return {
                "success": True,
                "data": pr_details
            }
        else:
            return {
                "success": False,
                "error": f"Failed to fetch pull requests. Status code: {response.status_code}",
                "message": response.json().get("message", "No error message provided")
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Network error occurred: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

def analyze_pr_with_llm(pr_details: Dict) -> str:

    if not pr_details.get("success", False):
        return f"Cannot analyze PR due to error: {pr_details.get('error', 'Unknown error')}"
        
    try:
        prs = pr_details["data"]
        if not prs:
            return "No pull requests found to analyze."
            
        analysis_results = []
        for pr in prs:
            # Basic PR analysis criteria
            title_length = len(pr["title"])
            has_description = bool(pr["body"])
            changed_files = pr.get("changed_files", 0)
            
            # Perform analysis
            feedback = []
            if title_length < 10:
                feedback.append("- Consider using a more descriptive title")
            if not has_description:
                feedback.append("- Adding a description would help reviewers understand the changes")
            if changed_files > 10:
                feedback.append("- Consider breaking down large PRs into smaller ones")
                
            if not feedback:
                feedback.append("- Well-structured PR with good documentation")
                
            analysis_results.append({
                "pr_number": pr["number"],
                "title": pr["title"],
                "feedback": feedback
            })
            
        # Format the analysis results
        result_text = "Pull Request Analysis:\n\n"
        for result in analysis_results:
            result_text += f"PR #{result['pr_number']}: {result['title']}\n"
            result_text += "\n".join(result['feedback']) + "\n\n"
            
        return result_text
        
    except KeyError as e:
        return f"Error analyzing PR: Missing required field - {str(e)}"
    except Exception as e:
        return f"Error analyzing PR: {str(e)}"

# Flask route handler (if using Flask)
def handle_fetch_pr_request(request):
    repo_url = request.args.get('repo_url')
    if not repo_url:
        return {"error": "Repository URL is required"}, 400
        
    pr_details = fetch_pr_from_github(repo_url)
    analysis = analyze_pr_with_llm(pr_details)
    
    return {
        "pr_details": pr_details,
        "analysis": analysis
    }