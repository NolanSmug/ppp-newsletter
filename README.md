# Ping Pong Parkinson Newsletter Relay Host

This is the host for the PingPongParkinson® NYC website's [newsletter page](https://www.pingpongnyc.org/newsletter)


## For future developers & maintainers

This repository holds a Python automation pipeline that fetches the latest newsletter email from a designated relay Gmail account's inbox, converts it to static HTML, and deploys it to GitHub Pages. The newsletter is then accessible [here](https://nolansmug.github.io/ppp-newsletter/).

### Website integration

The generated GitHub Pages site is embedded directly into the PingPongParkinson® NYC Squarespace site using this code block:

```html
<iframe src="[https://nolansmug.github.io/ppp-newsletter/](https://nolansmug.github.io/ppp-newsletter/)" width="100%" height="1200px" style="border:none; overflow:hidden;"></iframe>
```

### Architecture

- [main.py](main.py): The entry point. Manages fetching the email and generating the webpage.
- [email_fetcher.py](email_fetcher.py): Handles the IMAP connection to the relay email's inbox, validates the sender, and returns the HTML content and sent date from the latest unread message.
- [html_builder.py](html_builder.py): Cleans Gmail message's raw HTML, collects the related images, generates the main `index.html`, and manages the `archive/` directory.
- [archive](./archive/)`: Directory that stores the generated HTML files for the recent past newsletters.
- [images](./images/): Directory where inline image attachments downloaded from the emails are saved so they can be hosted locally.

#### Dependencies
- `BeautifulSoup4:` A Python library used in `html_builder.py` to parse, navigate, and modify the messy raw email HTML into a clean webpage structure.

### Environment variables and secrets

The pipeline requires three repository secrets to run. Configure these in GitHub under Settings > Secrets and variables > Actions:

- `EMAIL_USER`: The email address of the relay account.
- `APP_PASSWORD`: The 16-character Google App Password for the relay account.
- `ALLOWED_SENDERS`: A comma-separated list of authorized sender emails (ex: sender1@example.com, sender2@example.com).

### Pipeline and deployment

Running the script locally only generates the files on your machine. The production deployment is handled automatically by GitHub Actions:

- **Update newsletter:** A scheduled (or manually triggered) action that runs `main.py` injecting the repository secrets. It commits any new HTML and image files directly to the main branch to trigger GitHub Pages deployment. This workflow's steps are in the [update.yml](./.github/workflows/update.yml) file.

- **GitHub Pages:** Pushing the new commit automatically triggers GitHub's internal pages-build-deployment job, which pushes the updated files to the live URL. If the live site shows old content after an update, wait for this deployment job to finish in the Actions tab.

See the Actions tab [here](https://github.com/nolansmug/ppp-newsletter/actions) on GitHub.

### Running locally

Requires Python 3.10 or higher.


1. Clone the repository and navigate to the directory
   ```bash
    git clone https://github.com/nolansmug/ppp-newsletter.git
    cd ppp-newsletter
   ```

2. Create the virtual environment and install dependencies
   ```bash
    python -m venv .venv
    source .venv/bin/activate  # For Windows use: .venv\Scripts\activate
    pip install -r requirements.txt
   ```

3. Set up the environment variables in your terminal
   ```bash
    export EMAIL_USER="your_email@gmail.com"
    export APP_PASSWORD="your_app_password"
    export ALLOWED_SENDERS="sender@example.com"
    ```
4. Run the script
   ```bash
   python main.py
   ```

> **Note:** The script searches for the latest unread email. To test the same email multiple times, you must mark it as unread in your Gmail inbox before each run.

