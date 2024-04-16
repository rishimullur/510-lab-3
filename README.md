# 510-lab-3
# Promptbase

Promptbase is a simple Streamlit app for storing and retrieving prompts. It allows users to create, edit, delete, and search prompts stored in a PostgreSQL database.

## Installation

1. Clone the repository:

```sh
git clone <repository_url>
cd Promptbase
```

2. Install dependencies:

```sh
pip install -r requirements.txt
```

## Configuration

Before running the app, make sure to set up the following environment variables:

- `DATABASE_URL`: The URL for your PostgreSQL database.

You can either set these environment variables directly or create a `.env` file in the root directory of the project and define them there.

## Usage

To run the app, use the following command:

```sh
streamlit run app.py
```

This will start the Streamlit app locally, and you can access it in your web browser at `http://localhost:8501`.

## Contributing

Contributions are welcome! If you have any ideas for improvements or find any issues, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
