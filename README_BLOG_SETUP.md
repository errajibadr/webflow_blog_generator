

# 1 -  Create a config file for the website

in the `website_configs` folder, create a config file for the website.

duplicate the `sample.yaml` file and rename it to the name of the website.

```yaml
website:
  name: sample-website
  domain: sample-website.com
  workspace: sample-website
  
hostinger:
  host: ftp.sample-website.com or xx.xx.xx.xx # Optional, defaults to ftp.{domain}
  username: ${HOSTINGER_FTP_USERNAME}  
  password: ${HOSTINGER_FTP_PASSWORD}  
  remote_dir: / 

export:
  method: auto  # Options: auto, ftp, selenium, simulate
  
content_generation:
  topics_file: topics/sample-topics.csv
  batch_size: 2 # number of blogs to generate at a given time
  max_concurrent: 3 # number of blogs to generate concurrently
  
# website_enricher: ## Legacy i think 
#   config_file: website_configs/blog_config.yaml 

blog_config:
  site:
    title: TechInsight - Exploring the Future of Technology
    ...

  social:
    instagram: https://instagram.com/techinsight
    ...

  contact:
    email: info@techinsight.com
    phone: +33 9 87 65 43 21

  seo:
    defaultTitle: TechInsight - Exploring the Future of Technology
    ...

  ui:
    backgroundColor: "#F5F7FA"
    ...

  blog:
    blogIndexBackground: src/assets/images/background/tech_pattern.webp
    ...
```

# 2 -  Generate the Target content for the website

in the `website_configs/topics` folder, create a csv file for the website.

from Semrush export target keywords for the website.

expected columns : 
Database,Keyword,Seed keyword,Page,Topic,Page type,Tags,Volume,Keyword Difficulty,CPC (USD),Competitive Density,Number of Results,Intent,SERP Features,Trend,Click potential,Content references,Competitors

but mandatory columns are : Keyword, Page, Topic, Volume, Keyword Difficulty, Intent, Content references, Competitors


# 3 -  Generate the FTP connection to the website

in the `website_configs/website_name.yaml` file, create the FTP connection to the website.

```yaml
HOSTINGER_FTP_USERNAME
HOSTINGER_FTP_PASSWORD
```


# 4 -  Run the pipeline

```bash
python main.py --website website_name  --all
```




