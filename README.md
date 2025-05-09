# Python (Flask) Web App with PostgreSQL

Artists Booking Venues powered by Python (Flask) and PostgreSQL Database.
There is no user authentication or per-user data stored.

![Screenshot of website landing page](./repo-thumbnail.png)

The project is designed for deployment on Azure App Service with a PostgreSQL flexible server. See deployment instructions below.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/john0isaac/flask-webapp-postgresql-db?devcontainer_path=.devcontainer/devcontainer.json)

![Architecture Diagram: App Service, PostgreSQL server.](./architecture-diagram.png)

## Local Development

1. **Download the project starter code locally**

    ```bash
    git clone https://github.com/john0isaac/flask-webapp-postgresql-db.git
    cd flask-webapp-postgresql-db
    ```

2. **Initialize and activate a virtualenv using:**

    ```bash
    python -m virtualenv venv
    source venv/bin/activate
    ```

    >**Note** - In Windows, the `venv` does not have a `bin` directory. Therefore, you'd use the analogous command shown below:

    ```bash
    source venv/Scripts/activate
    deactivate
    ```

3. **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Run the development server:**

    ```bash
    export FLASK_APP=app.py
    export FLASK_ENV=development
    export FLASK_DEBUG=true
    flask run --reload
    ```

5. **Verify on the Browser**

Navigate to project homepage [http://127.0.0.1:5000/](http://127.0.0.1:5000/) or [http://localhost:5000](http://localhost:5000)

## Azure Deployment

This repository is set up for deployment on Azure App Service (w/PostgreSQL flexible server) using the configuration files in the `infra` folder.

To deploy your own instance, follow these steps:

1. Sign up for a [free Azure account](https://azure.microsoft.com/free/)

2. Install the [Azure Dev CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd).

3. Initialize a new `azd` environment:

    ```shell
    azd init
    ```

    It will prompt you to provide a name (like "flask-app") that will later be used in the name of the deployed resources.

4. Provision and deploy all the resources:

    ```shell
    azd up
    ```

    It will prompt you to login, pick a subscription, and provide a location (like "eastus"). Then it will provision the resources in your account and deploy the latest code. If you get an error with deployment, changing the location (like to "centralus") can help, as there may be availability constraints for some of the resources.

5. When azd has finished deploying, you'll see an endpoint URI in the command output. Visit that URI to browse the app! 🎉

If you make any changes to the app code, you can just run this command to redeploy it:

```shell
azd deploy
```

## Security

It is important to secure the databases in web applications to prevent unwanted data access.
This infrastructure uses the following mechanisms to secure the PostgreSQL database:

* Azure Firewall: The database is accessible only from other Azure IPs, not from public IPs. (Note that includes other customers using Azure).
* Admin Username: A unique string generated based on the resource name (not random, but not a standard name, either).
* Admin Password: Randomly generated and updated on each deploy.
* PostgreSQL Version: Latest available on Azure, version 14, which includes security improvements.

⚠️ For even more security, consider using a Key Vault to store your database username and password plus an Azure Virtual Network to connect the Web App to the Database.

## Costs

Pricing varies per region and usage, so it isn't possible to predict exact costs for your usage.

You can try the [Azure pricing calculator](https://azure.microsoft.com/pricing/calculator/) for the resources:

* Azure App Service: Free Tier with shared CPU cores, 1 GB RAM. [Pricing](https://azure.microsoft.com/pricing/details/app-service/linux/)
* PostgreSQL Flexible Server: Burstable Tier with 1 CPU core, 32GB storage. Pricing is hourly. [Pricing](https://azure.microsoft.com/pricing/details/postgresql/flexible-server/)

⚠️ To avoid unnecessary costs, remember to take down your app if it's no longer in use,
either by deleting the resource group in the Portal or running `azd down`.

## Google Cloud Deployment

1. Open the Google Cloud Shell and execute the following command:

    ```shell
    git clone https://github.com/john0isaac/flask-webapp-postgresql-db.git
    cd flask-webapp-postgresql-db
    ```

2. Create the env_variables.yaml file that contains your secret environment variables.

    ```shell
    nano env_variables.yaml
    ```

3. Add your Google Cloud SQL database connection details

    ```shell
    env_variables:
      DB_USER_NAME: 'secret'
      DB_PASSWORD: 'secret'
      DB_NAME: 'secret'
      DB_HOST: '111.111.111.111'
      DB_PORT: '5432'
      DB_CONNECTOR: 'postgresql+pg8000'
      INSTANCE_UNIX_SOCKET: '/cloudsql/Connection name'
      DEPLOYMENT_LOCATION: 'gcp'
    ```

4. save and exit the file CTRL+x followed by y followed by Enter.

5. Deploy the web application.

    ```shell
    gcloud app deploy app.yaml
    ```

### Deploying After Deleting Everything from Google Cloud

1. Create a Cloud SQL instance using the following parameters:

    * Specify instance name and password.
    * Select production instead of production plus.
    * Select Single Zone.
    * Specify the machine configuration of 2 vCPUs and 8 GB Memory.
    * Select the smallest storage option available 10 GB.
    * Add your IP to the Instance Network.
    * Select Create.
    * Create a database and call it fyyur.
    * Create a user and call it john.
    * Grant All privileges to user john.

2. Import Data dump.
3. Pull the code to the Cloud Shell.
4. Create environment variables .yaml file.
5. Enable App Engine.
6. execute the following command `gcloud beta app repair`.
7. execute the following command `gcloud app deploy --no-cache`.
