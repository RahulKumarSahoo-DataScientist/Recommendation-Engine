# Importing all required libraries, modules
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer # term frequency - inverse document frequncy is a numerical statistic that is intended to reflect how important a word is to document in a collecion or corpus
# from sklearn.metrics.pairwise import linear_kernel
from sklearn.metrics.pairwise import cosine_similarity
import joblib
from sqlalchemy import create_engine
from urllib.parse import quote

# import Dataset 
game = pd.read_csv(r"game.csv", encoding = 'utf8')

# Database Connection

# Upload the Table into Database

user = "root" # user
pw = "dba@123#" # passwrd
db = "amerdb" # database

# engine = create_engine(f'mysql+pymysql://{user_name}:%s@localhost:3306/{database}' % quote(f'{your_password}'))
engine = create_engine(f"mysql+pymysql://{user}:%s@localhost/{db}" % quote(f'{pw}'))
                  

game.to_sql('game', con = engine, if_exists = 'replace', chunksize = 1000, index = False)


# Read the Table (data) from MySQL database

# sql = 'SELECT * FROM anime_new'
# anime_new = pd.read_sql_query(sql, con = engine)


sql = 'SELECT * FROM game'
game = pd.read_sql_query(sql , con = engine)

# Check for Missing values
game["game"].isnull().sum() 

# Impute the Missing values in 'genre' column for a movie with 'General' category
game["game"] = game["game"].fillna("General")


# remove duplicates
game["game"].drop_duplicates(inplace=True)


# Create a Tfidf Vectorizer to remove all stop words

tfidf = TfidfVectorizer(stop_words = "english")   # taking stop words from tfidf vectorizer 

# Transform a count matrix to a normalized tf-idf representation
tfidf_matrix = tfidf.fit(game.game)   

# Save the Pipeline for tfidf matrix

joblib.dump(tfidf_matrix, 'matrix')

os.getcwd()

mat = joblib.load("matrix")

tfidf_matrix = mat.transform(game.game)

tfidf_matrix.shape #12294, 47

# cosine(x, y)= (x.y⊺) / (||x||.||y||)
# Computing the cosine similarity on Tfidf matrix

cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

joblib.dump(cosine_sim_matrix, 'cosine_matrix')
cosine_sim_matri = joblib.load('cosine_matrix')
# Create a mapping of anime name to index number
game_index = pd.Series(game.index, index = game['game']).drop_duplicates()

# Example
game_id = game_index["SoulCalibur"]

game_id

# Custom Function to Find the TopN Movies to be Recommended

def get_recommendations(Titles, topN):    
    # topN = 10
    # Getting the movie index using its title 
    game_id = game_index[Titles]
    
    # Getting the pair wise similarity score for all the anime's with that 
    # anime
    cosine_scores = list(enumerate(cosine_sim_matrix[game_id]))
    
    # Sorting the cosine_similarity scores based on scores 
    cosine_scores = sorted(cosine_scores, key = lambda x:x[1], reverse = True)
    
    # Get the scores of top N most similar movies 
    cosine_scores_N = cosine_scores[0: topN + 1]
    
    # Getting the movie index 
    game_idx  =  [i[0] for i in cosine_scores_N]
    game_scores =  [i[1] for i in cosine_scores_N]
    
    # Similar movies and scores
    game_similar_show = pd.DataFrame(columns = ["game","rating"])
    game_similar_show["game"] = game.loc[game_idx, "game"]
    game_similar_show["rating"] = game.loc[game_idx, "rating"]
    game_similar_show["Score"] = game_scores
    game_similar_show.reset_index(inplace = True)  
    # anime_similar_show.drop(["index"], axis=1, inplace=True)
    return(game_similar_show.iloc[1:, ])

rec = get_recommendations("NFL 2K1", topN = 10)

rec

