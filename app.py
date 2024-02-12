from flask import Flask, render_template, request
import pandas as pd
import joblib
from sqlalchemy import create_engine
from urllib.parse import quote
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

user = 'root'
pw = 'dba@123#'
db = 'amerdb'

engine = create_engine(f"mysql+pymysql://{user}:%s@localhost/{db}" % quote(f'{pw}'))

sql='SELECT * FROM game'
game = pd.read_sql_query(sql , con = engine)

# Check for Missing values
game["game"].isnull().sum() 

# Impute the Missing values in 'genre' column for a movie with 'General' category
game["game"] = game["game"].fillna("General")
game_list = game["game"].to_list()

tfidf = joblib.load('matrix')

tfidf_matrix = tfidf.transform(game.game)

cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

game_index = pd.Series(game.index, index = game['game']).drop_duplicates()


### Custom Function ###
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
######End of the Custom Function######    

@app.route('/')
def home():
    return render_template("index.html", game_list = game_list )

@app.route('/guest', methods = ["post"])
def Guest():
    if request.method == 'POST' :
        mn = request.form["mn"]
        tp = request.form["tp"]
        
        top_n = get_recommendations(mn, topN = int(tp))
        # connection to a database
                
        # Transfering the file into a database by using the method "to_sql"
        
        top_n.to_sql('topN_rec', con = engine, if_exists = 'replace', chunksize = 1000, index= False)
        
        html_table = top_n.to_html(classes='table table-striped')
        return render_template( "data.html", Y = "Results have been saved in your database", Z =  f"<style>\
                    .table {{\
                        width: 50%;\
                        margin: 0 auto;\
                        border-collapse: collapse;\
                    }}\
                    .table thead {{\
                        background-color: #39648f;\
                    }}\
                    .table th, .table td {{\
                        border: 1px solid #ddd;\
                        padding: 8px;\
                        text-align: center;\
                    }}\
                        .table td {{\
                        background-color: #5e617d;\
                    }}\
                            .table tbody th {{\
                            background-color: #ab2c3f;\
                        }}\
                </style>\
                {html_table}") 

if __name__ == '__main__':

    app.run(debug = True)