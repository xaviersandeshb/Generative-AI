
from langgraph.graph import  END, Graph
import google.generativeai as genai
import os
import requests
import urllib3
import json
from dotenv import load_dotenv
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
import time
console = Console()

from langchain_community.utilities import OpenWeatherMapAPIWrapper
load_dotenv()
os.environ["OPENWEATHERMAP_API_KEY"] = os.environ.get("OPENWEATHERMAP_API_KEY")
weather = OpenWeatherMapAPIWrapper()
api_key = os.getenv("API_KEY")
api_url = os.getenv("API_URL")
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")




def show_loading_animation(message,steps=None):
    if not steps:
        steps = [
            ("Processing...", "dots"),
            ("Analyzing data...", "line"),
            ("Preparing response...", "dots2")
        ]
    
    console.print("\n")
    for step, spinner in steps:
        with console.status(f"[bold blue]{step}", spinner=spinner):
            time.sleep(0.7)
    console.print("\n")

def aqi(city):
    wapi_key = os.getenv("openweathermap_api_key") 
    latlonurl = f'http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={wapi_key}'
    response1 = requests.get(latlonurl)
    lldata= response1.json() 
    lat = lldata[0]['lat']
    lon = lldata[0]['lon']

    aiqurl = f'http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={wapi_key}'
    response2 = requests.get(aiqurl)
    aiqdata = response2.json()
   # print(aiqdata['list'][0]['main']['aqi'])
    aiq = aiqdata['list'][0]['main']['aqi']
    qi = ['Good','Fair','Moderate','Poor','Very Poor']
    if aiq == 1:
        quality = qi[0] 
    elif aiq == 2:
        quality = qi[1]       
        
    elif aiq == 3:
        quality = qi[2]    
        
    elif aiq == 4:
        quality = qi[3]   
    elif aiq == 5:
        quality = qi[4]     
    
   # print("air quality is ",quality)
    return quality

def disttime(s, d):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    gm_key = os.getenv('google_api_key')
    url = f'https://maps.googleapis.com/maps/api/distancematrix/json?origins={s}&destinations={d}&key={gm_key}'
    try:
        r = requests.get(url, verify=False)
        response_data = r.json()

        if response_data['status'] == 'OK':
            dist = response_data['rows'][0]['elements'][0]['distance']['text']
            dur = response_data['rows'][0]['elements'][0]['duration']['text']
            return dist, dur
        else:
            return None, f"Error: {response_data['status']}"
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {e}"

def intro(arg=None):
    console.print(Panel("[bold cyan]Welcome to Smart Travel Assistant![/bold cyan]\n[italic]I'm here to help you plan your perfect trip! 🌍✈️[/italic]", 
                       border_style="cyan"))
    return 0

location =''
def fetchcity(arg=None):
    console.print("\n[bold green]Travel Assistant:[/bold green] [italic]Can you tell me the name of the city you're interested in? 😊[/italic]")
    user_input = input("\tYour response: ")
    #prompt1 = f"Your task is to extract only the city name from the given input. If no city name is mentioned, return 'None'. Following is the input: {user_input}"
    extraction_prompt = f"""
        Task: Extract the city name from the following user input.
        Input: "{user_input}"
        
        Requirements:
        - If multiple cities are mentioned, identify the main destination
        - If no city is mentioned, return 'None'
        - Correct common misspellings
        - Return only the city name without any additional text
        
        City name:
        """
    response1 = model.generate_content(extraction_prompt)
    city_name = response1.text.strip()
    global location
    location = city_name.lower()
    return location

finalLocation =''
def validatecity(cityname):
    prompt = f"Your task is to check if the given text is a valid city name. If it's a valid city name, return it. Otherwise, return 'None'. Following is the input: {cityname}"
    response = model.generate_content(prompt)
    verified_city_name = response.text.strip()
    #print("validating city name ",verified_city_name)
    check = ''
    if location.lower() == verified_city_name.lower():
        if verified_city_name!="None":
            check = 'valid'
            global finalLocation
            finalLocation = verified_city_name
            return check
    else:
        check = 'invalid'
        return check
 
route =0   
def router(datainput):
    #print("router entered")
    #print(location , verified_city_name)
    if datainput == 'valid':
        global route
        route = "valid"
        console.print("\n")
        with console.status("[bold green]Initializing travel planner...", spinner="dots"):
            time.sleep(0.8)
        
        console.print(Panel(
            f"""
            [bold green]✓ Ready to Plan Your Journey![/bold green]
            
            [cyan]Status:[/cyan] All systems go! 🚀
            [cyan]Next:[/cyan] Fetching destination details...
            """,
            border_style="green",
            title="[bold green]🎯 Navigation Status[/bold green]"
        ))
       # print("router says", route)
    else:
        route = "invalid"
        console.print("\n")
        with console.status("[bold red]Checking status...", spinner="dots"):
            time.sleep(0.8)
        
        console.print(Panel(
            f"""
            [bold red]⚠ Location Verification Failed[/bold red]
            
            [yellow]We couldn't proceed with the current location.[/yellow]
            
            [italic]What you can do:[/italic]
            • Double-check the city name
            • Try entering it again
            • Use a different nearby city
            
            [bold cyan]↺ Redirecting to city selection...[/bold cyan]
            """,
            border_style="red",
            title="[bold red]⚠ Navigation Alert[/bold red]"
        ))
       # print("\n\tTravel Assistant: Looks like you've entered an invalid city Name....\n")
       # print("router says", route)
        
    return route        

def fetchCityWeatherCond(data=None):
    city = finalLocation
    
    weather_steps = [
        ("Checking current weather...", "dots"),
        ("Analyzing air quality...", "line"),
        ("Preparing weather report...", "dots2")
    ]
    show_loading_animation("", weather_steps)
    
    airindex = aqi(city)
    weather_data = weather.run(city)

    query = f'''
    As a friendly travel advisor, provide a brief assessment of {city}'s current conditions:
    Weather: {weather_data}
    Air Quality: {airindex}

    Give 3 key points about:
    1. Current weather impact on tourism
    2. Best outdoor activity times today
    3. One important health/safety tip

    Keep it conversational and brief. Use relevant emojis.
    '''
    
    val = model.generate_content(query)
    
    # Create concise weather panel
    weather_summary = f"""
    [bold cyan]TODAY IN {city.upper()}[/bold cyan]
    
    🌡️ {weather_data}
    💨 Air Quality: {airindex}
    """
    
    # Create brief analysis panel
    analysis = f"""
    {val.text}
    """
    
    console.print(Panel(
        weather_summary + "\n\n" + analysis,
        border_style="cyan",
        title="[bold cyan]📍 Quick Weather Update[/bold cyan]"
    ))

    return city, weather_data

def fetchFeatures(userdata):
    # user = input(f"""\n\tTravel Assistant: What do you want to know about {userdata[0]}? I can help with travel plans, clothing 
    # suggestions, tourist spots, or the best time to visit. Just let me know!\n\n\t""")
    cityName = userdata[0]
    feature_menu = f"""
    [bold cyan]AVAILABLE FEATURES FOR {cityName.upper()}[/bold cyan]
    
    [bold]Choose what you'd like to know:[/bold]
    
    🗺️  Travel Plans & Routes
    🎯  Tourist Spots & Local Secrets
    👔  Packing & Clothing Guide
    📅  Best Time to Visit
    
    [italic]Share your interest or ask any travel-related question![/italic]
    """
    
    console.print(Panel(
        feature_menu,
        border_style="cyan",
        title="[bold cyan]✨ Travel Assistant[/bold cyan]"
    ))
    
    user = input("\tYour choice: ")
    
    query = f"""
You are a smart travel assistant that helps users with travel-related information.
Your task is to analyze the user's input and perform the following:

1. If the input contains a city or country name, return the city name or country name (whichever is found).
2. Based on the input, determine if the user is asking about:
    - Travel plans (e.g., trips, travels to/from a location, vacation, itinerary, etc.)
    - Clothing suggestions (e.g., what to wear, clothing advice, dressing recommendations, etc.)
    - Tourist spots (e.g., tourist attractions, places to visit, must-see spots, etc.)
3. Return one of these keywords: "travel plans", "clothing suggestions", or "tourist spots", or "best time to visit" based on what the input is related to.
4. If the input does not contain a city name or relate to any of the above topics, simply respond based on the content of the query (e.g., greetings, questions, or other types of messages).

Return the response in a dictionary format with the following keys:
- "city": (string, city or country name found in the input),
- "response": (string, one of the keywords: "travel plans", "clothing suggestions", "tourist spots"),
- "related_keywords": (list, any relevant keywords detected in the input related to the categories above).

Following is the user's input:
{user}
"""
    result = model.generate_content(query)
    data = json.loads((result.text[7:-4]))
    city = data.get('city')
    res = data.get('response')
    kw = data.get('related_keywords')
    #print(city , res, kw)
    
    return city,res,userdata
          
def router3(userinput): 
    response = userinput[1]  
    #print("router3 input ", userinput[1])
    options = ['travel plans','tourist spots','clothing suggestions','best time to visit']
    #if city.lower() == fetchedcity.lower():
    
    console.print("\n")
    with console.status("[bold cyan]Routing your request...", spinner="dots"):
        time.sleep(0.8)
   
    if response == options[0]:
            route = "n5"
            #print(route)
            message = {
            "title": "🗺️ Travel Planning",
            "status": "Preparing route and transportation options",
            "action": "Creating your personalized travel plan"
        }
            #return route
    elif response == options[1]:
            route = "n6"
            message = {
            "title": "🎯 Local Exploration",
            "status": "Gathering insider recommendations",
            "action": "Finding the best spots to visit"
        }
            #print(route)
            #return route
    elif response == options[2]:
            route = "n7"
            message = {
            "title": "👔 Packing Assistant",
            "status": "Analyzing weather and local customs",
            "action": "Creating your custom packing list"
        }
            #print(route)
            #return route
    elif response == options[3]:
            route = "n8"
            message = {
            "title": "📅 Timing Guide",
            "status": "Checking seasonal patterns",
            "action": "Finding the perfect time for your visit"
        }
            
            
    console.print(Panel(
        f"""
        [bold cyan]{message['title']}[/bold cyan]
        
        [green]Status:[/green] {message['status']} ✓
        [green]Next:[/green] {message['action']}
        
        [italic cyan]Please wait while we prepare your information...[/italic cyan]
        """,
        border_style="cyan",
        title="[bold cyan]🔄 Request Routed[/bold cyan]"
    ))        
    
    time.sleep(0.5)        #print(route)
    return route    
  
def travelplan(userinput):
    destination = userinput[0]
    console.print("\n[bold green]Travel Assistant:[/bold green] [italic]Please enter your current location:[/italic]")
    source = input("\tYour location: ")
    sw = weather.run(source)
    dw = weather.run(destination)
    travel = disttime(source,destination)
    distance = travel[0]
    timetaken = travel[1]
    
    route_steps = [
        ("Calculating route...", "dots"),
        ("Checking travel conditions...", "line"),
        ("Planning journey...", "dots2")
    ]
    show_loading_animation("", route_steps)
    
    console.print(Panel(f"""
[bold cyan]TRAVEL PLAN DETAILS[/bold cyan]
[bold]From:[/bold] {source}
[bold]To:[/bold] {destination}
[bold]Distance:[/bold] {distance}
[bold]Estimated Time:[/bold] {timetaken}
""", border_style="blue"))
    
    # query = f'''Given the weather conditions for {source} ({sw}) and {destination} ({dw}), 
    # as well as the distance{distance} and travelling time{timetaken} between the two locations, 
    # provide the following information in plain text, following the format below:
    # 1. The most suitable mode of transport based on both the weather conditions and the travel time.
    # 2. Any travel tips considering the weather conditions.'''
    
    weather_prompt = f"""
    Looking at the journey from {source} to {destination}:
    
    Source: {sw}
    Destination: {dw}
    Travel: {travel[0]}, {travel[1]}

    Provide:
    1. Best way to travel
    2. One key travel tip
    3. One weather-related advice

    Keep it friendly and brief. Use emojis.
    """
    
    response = model.generate_content(weather_prompt)
    # console.print("[bold green]Travel Recommendations:[/bold green]")
    # console.print(f"[italic]{response.text}[/italic]")
    console.print(Panel(f"""
    [bold cyan]Your Travel Plan[/bold cyan]
    
    [bold]Journey Details:[/bold]
    📍 From: {source}
    🎯 To: {destination}
    🛣️ Distance: {travel[0]}
    ⏱️ Duration: {travel[1]}
    
    [bold]Analysis & Recommendations:[/bold]
    {response.text}
    """, border_style="blue"))
    return userinput

def touristspots(input):
    cityName = input[2][0]
    #query = f"Provide a list of popular tourist spots in {cityName} along with a brief description of each. Additionally, create a schedule to cover all the spots in one day, with approximate visit times for each location. Keep the response clear, brief, and in bullet points."
    
        # Tourist spots animation
    spots_steps = [
        ("Discovering local favorites...", "dots"),
        ("Finding hidden gems...", "line"),
        ("Curating best spots...", "dots2")
    ]
    show_loading_animation("", spots_steps)
    
    spots_prompt = f"""
    As a local guide, recommend for {cityName}:

    1. Top 3 must-visit spots (not the obvious tourist traps)
    2. One hidden gem locals love
    3. Best area for food

    Keep each recommendation to 1-2 sentences. Add relevant emojis.
    """
    response = model.generate_content(spots_prompt)
    # console.print(Panel(f"[bold cyan]TOURIST SPOTS IN {cityName.upper()}[/bold cyan]\n[italic]{response.text}[/italic]", 
    #                    border_style="cyan"))
    console.print(Panel(
        f"[bold cyan]🎯 EXPLORING {cityName.upper()}[/bold cyan]\n\n[italic]{response.text}[/italic]",
        border_style="cyan"
    ))
    return input

def clothsuggestions(input):
    cityName = input[2][0]
    wd = input[2][1]
    #query = f"Based on the current weather {wd}in {cityName}, provide short, clear clothing suggestions in bullet points for both men and woman separately. Focus on comfort, style, and practicality."
    
    packing_steps = [
        ("Checking weather conditions...", "dots"),
        ("Considering local culture...", "line"),
        ("Creating packing list...", "dots2")
    ]
    show_loading_animation("", packing_steps)
    clothing_prompt = f"""
    Given the weather in {cityName} ({wd}), suggest a minimal but complete packing list for both men and women.

    Focus on:
    1. 3-4 essential items
    2. 1 weather-specific item
    3. 1 local culture tip

    Keep it brief and practical. Use emojis for categories.
    """
    response = model.generate_content(clothing_prompt)
    # console.print(Panel(f"[bold cyan]CLOTHING SUGGESTIONS FOR {cityName.upper()}[/bold cyan]\n[italic]{response.text}[/italic]", 
    #                    border_style="magenta"))
    console.print(Panel(
        f"[bold magenta]👔 PACKING GUIDE FOR {cityName.upper()}[/bold magenta]\n\n[italic]{response.text}[/italic]",
        border_style="magenta"
    ))
    return input

def best_time_to_visit(input):
    cityName = input[2][0]
    #query = f"best time to visit {cityName}. respond with plain text without any special symbols and in a short bulleted summary"
    timing_steps = [
        ("Analyzing seasonal patterns...", "dots"),
        ("Checking events calendar...", "line"),
        ("Finding perfect timing...", "dots2")
    ]
    show_loading_animation("", timing_steps)
    timing_prompt = f"""
    For {cityName}, briefly share:

    1. Best month to visit and why
    2. One month to avoid and why
    3. Money-saving tip about timing

    Keep it conversational and short. Use emojis.
    """
    response = model.generate_content(timing_prompt)
    # console.print(Panel(f"[bold cyan]BEST TIME TO VISIT {cityName.upper()}[/bold cyan]\n[italic]{response.text}[/italic]", 
    #                    border_style="green"))
    console.print(Panel(
        f"[bold green]🗓️ BEST TIME TO VISIT {cityName.upper()}[/bold green]\n\n[italic]{response.text}[/italic]",
        border_style="green"
    ))

def end_session(input_data=None):
    # Ending animation steps
    ending_steps = [
        ("Saving session details...", "dots"),
        ("Finalizing recommendations...", "line"),
        ("Wrapping up...", "dots2")
    ]
    
    show_loading_animation("", ending_steps)
    
    # Farewell message with summary
    farewell_message = f"""
    [bold green]✨ Thank You for Using Smart Travel Assistant![/bold green]
    
    [cyan]Session Summary:[/cyan]
    🎯 Destination Explored: [bold]{finalLocation.title()}[/bold]
    
    [bold]Your Travel Package:[/bold]
    • Weather and conditions checked
    • Local recommendations provided
    • Travel tips customized
    
    [italic green]We hope you have a wonderful journey![/italic green]
    
    [bold cyan]Safe Travels! 🌟[/bold cyan]
    
    [dim]Type 'start' to plan another journey...[/dim]
    """
    
    # Create a decorative border
    border_style = "bold cyan"
    console.print("\n")
    console.print("=" * 60, style=border_style)
    console.print("\n")
    
    # Display farewell panel
    console.print(Panel(
        farewell_message,
        border_style="cyan",
        title="[bold cyan]🌍 Journey Planning Complete[/bold cyan]",
        subtitle="[cyan]Thank you for traveling with us![/cyan]"
    ))
    
    # Bottom border
    console.print("\n")
    console.print("=" * 60, style=border_style)
    console.print("\n")
    
    return END




#node ids 
n1 = "fetchcity"
n2 = "validatecity"
n3 = "fetchcityTemperature"
n4 = "Fetch features"
n5 ="travel plan" 
n6 = "tourist spots" 
n7 = "cloth suggestions"
n8 = "besttimetolocation"

app = Graph()
app.add_node("entry",intro)
app.add_node(n1,fetchcity)
app.add_node(n2,validatecity)
app.add_node(n3,fetchCityWeatherCond)
app.add_node(n4,fetchFeatures)
app.add_node(n5,travelplan)
app.add_node(n6,touristspots)
app.add_node(n7,clothsuggestions)
app.add_node(n8,best_time_to_visit)
app.add_node("end", end_session)


app.set_entry_point("entry")

app.add_edge("entry",n1)
app.add_edge(n1,n2)
app.add_conditional_edges(
    n2,router,{"valid":n3,"invalid":n1}
)

app.add_edge(n3,n4)

app.add_conditional_edges(
    n4,router3,{"n5":n5,"n6":n6,"n7":n7,"n8":n8}
)

app.add_edge(n5,n8)
app.add_edge(n6,n8)
app.add_edge(n7,n8)
app.add_edge(n8,"end")

appflow = app.compile()


result = appflow.invoke("hi")