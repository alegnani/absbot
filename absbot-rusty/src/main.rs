use anyhow::{anyhow, Context};
use chrono::{self, Local, NaiveDateTime, NaiveTime, TimeZone};
use reqwest::blocking;
use reqwest::header::{
    HeaderMap, HeaderValue, ACCEPT, ACCEPT_ENCODING, AUTHORIZATION, CONNECTION, CONTENT_LENGTH,
    HOST, ORIGIN, REFERER,
};
use reqwest::StatusCode;
use std::io;
use std::process::Child;
use std::process::Command;
use std::{thread, time::Duration};
use thirtyfour_sync::prelude::*;

fn main() {
    if let Err(e) = run() {
        eprintln!("{}", e);
    }

    println!();
    println!("Press ENTER to exit AbsBot");
    io::stdin().read_line(&mut "".into()).expect("Error");
}

fn run() -> anyhow::Result<()> {
    let (hour, minute, lesson_id) = get_input()?;

    println!("Got input");

    let process = start_webdriver();
    println!("Webdriver started");

    let auth_token = get_auth_token()?;

    println!("Got authentication token");

    let target = wait_for_target(hour, minute)?;

    let outcome = make_request(auth_token, lesson_id, target);

    match outcome {
        Ok(status) if status == StatusCode::CREATED => {
            println!("\n-----Could get a place, enjoy :)-----")
        }
        Ok(_) => println!("There were no places left :("),
        Err(_) => println!("Something went wrong with the request :("),
    }

    stop_webdriver(process);

    Ok(())
}

fn get_auth_token() -> anyhow::Result<String> {
    let caps = DesiredCapabilities::chrome();
    let driver =
        WebDriver::new("http://localhost:4444", &caps).context("Could not find Webdriver")?;
    driver
        .get("https://schalter.asvz.ch/")
        .context("Could not connect to asvz's website")?;
    loop {
        if let Ok(url) = driver.current_url() {
            if url == "https://schalter.asvz.ch/tn/memberships" {
                break;
            }
        }
        thread::sleep(Duration::from_secs(1));
    }
    thread::sleep(Duration::from_secs(1));

    let key = driver
        .execute_script("return localStorage.key(0)")
        .context("Could not fetch the json key")?
        .convert::<String>()
        .context("Could not parse the json key")?;

    let raw_json: String = driver
        .execute_script(&format!("return localStorage.getItem('{}')", key))
        .context("Could not fetch the raw JSON data")?
        .value()
        .as_str()
        .context("The raw JSON is not in String format")?
        .into();

    let parsed_json = serde_json::from_str::<serde_json::Value>(&raw_json)
        .context("Could not parse the raw JSON")?;
    let auth_token = parsed_json["access_token"]
        .as_str()
        .context("No field 'access_token' in the JSON")?;

    Ok(auth_token.into())
}

fn wait_for_target(hour: u32, minute: u32) -> anyhow::Result<u64> {
    let now = Local::now();
    let target_time = NaiveTime::from_hms(hour, minute, 0);
    let target_date = now.date().naive_local();
    let target = chrono::Local
        .from_local_datetime(&NaiveDateTime::new(target_date, target_time))
        .single()
        .map(|time| time.timestamp_millis() as u64 + 1)
        .context("Error converting date time")?;

    println!("Computed target time: {}", target);

    let mut dt = 0;
    if now.timestamp_millis() as u64 <= target {
        dt = target - now.timestamp_millis() as u64;
    }

    if dt > 3000 {
        println!("Going to sleep for {} seconds", dt / 1000 - 3);
        thread::sleep(Duration::from_millis(dt - 3000));
    }

    println!("Waking up...");

    println!("Busy waiting to send request...");

    while (Local::now().timestamp_millis() as u64) < target {}
    
    Ok(target)
}

fn make_request(auth_token: String, lesson_id: u32, target: u64) -> anyhow::Result<StatusCode> {
    let url = format!(
        "https://schalter.asvz.ch/tn-api/api/Lessons/{}/enroll??t={}",
        lesson_id, &target
    );
    let client = blocking::Client::new();
    let request = client
        .post(url)
        .body("{}")
        .headers(construct_headers(auth_token, lesson_id).context("Error creating headers")?);
    let response = request.send().expect("Something went wrong :(");
    Ok(response.status())
}

fn construct_headers(auth_token: String, lesson_id: u32) -> anyhow::Result<HeaderMap> {
    let mut headers = HeaderMap::new();

    let auth = HeaderValue::from_str(&format!("Bearer {}", auth_token))
        .context("Could not create Authorization header entry")?;
    let referer = HeaderValue::from_str(&format!(
        "https://schalter.asvz.ch/tn/lessons/{}",
        lesson_id
    ))
    .context("Could not create Referer header entry")?;
    let connection = HeaderValue::from_static("keep-alive");
    let cont_len = HeaderValue::from_static("2");
    let host = HeaderValue::from_static("schalter.asvz.ch");
    let origin = HeaderValue::from_static("https://schalter.asvz.ch");
    let accept = HeaderValue::from_static("application/json, text/plain, */*");
    let encoding = HeaderValue::from_static("gzip, deflate, br");

    headers.insert(ACCEPT, accept);
    headers.insert(ACCEPT_ENCODING, encoding);
    headers.insert(AUTHORIZATION, auth);
    headers.insert(CONNECTION, connection);
    headers.insert(CONTENT_LENGTH, cont_len);
    headers.insert(REFERER, referer);
    headers.insert(HOST, host);
    headers.insert(ORIGIN, origin);
    Ok(headers)
}

fn start_webdriver() -> Child {
    Command::new("chromedriver.exe")
        .arg("--port=4444")
        .spawn()
        .expect("Could not start webdriver")
}

fn stop_webdriver(mut process: Child) {
    match process.kill() {
        Ok(_) => println!("Webdriver shut down"),
        Err(_) => println!("Webdriver shut down(not gracefully)"),
    }
}

fn get_input() -> anyhow::Result<(u32, u32, u32)> {
    let mut hour = String::new();
    let mut minute = String::new();
    let mut lesson_id = String::new();
    println!("Enter hour [0-23]: ");
    io::stdin()
        .read_line(&mut hour)
        .context("Error whilst reading input")?;
    let hour = hour
        .trim()
        .parse::<u32>()
        .context("Invalid entry for hour")?;
    if hour > 23 {
        return Err(anyhow!("Hour not in specified interval"));
    }

    println!("Enter minute [0-59]: ");

    io::stdin()
        .read_line(&mut minute)
        .context("Error whilst reading input")?;

    let minute = minute
        .trim()
        .parse::<u32>()
        .context("Invalid entry for minute")?;

    if minute > 59 {
        return Err(anyhow!("Minute not in specified interval"));
    }

    println!("Enter lesson_id [xxxxxx]: ");

    io::stdin()
        .read_line(&mut lesson_id)
        .context("Error whilst reading input")?;

    let lesson_id = lesson_id
        .trim()
        .parse::<u32>()
        .context("Invalid entry for lesson_id")?;

    if minute > 999999 {
        return Err(anyhow!("Lesson_id not in specified interval"));
    }

    Ok((hour, minute, lesson_id))
}
