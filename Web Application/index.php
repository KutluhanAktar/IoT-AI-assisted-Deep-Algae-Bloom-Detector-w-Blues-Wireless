<?php

# Include the Twilio PHP Helper Library.
require_once '../twilio-php-main/src/Twilio/autoload.php'; 
use Twilio\Rest\Client;

# Define the Twilio account information.
$account = array(	
				"sid" => "<_SID_>",
				"auth_token" => "<_AUTH_TOKEN_>",
				"registered_phone" => "+__________",
				"verified_phone" => "+14155238886"
		   );
		
# Define the Twilio client object.
$twilio = new Client($account["sid"], $account["auth_token"]);

# Send a WhatsApp text message from the verified phone to the registered phone.
function send_text_message($twilio, $account, $text){
	$message = $twilio->messages 
              ->create("whatsapp:".$account["registered_phone"],
                        array( 
                            "from" => "whatsapp:".$account["verified_phone"],       
                            "body" => $text							
                        ) 
              );
			  
    echo '{"body": "WhatsApp Text Message Send..."}';
}

# If requested, send a WhatsApp media message from the verified phone to the registered phone.
function send_media_message($twilio, $account, $text, $media){
	$message = $twilio->messages 
              ->create("whatsapp:".$account["registered_phone"],
                        array( 
                            "from" => "whatsapp:".$account["verified_phone"],       
                            "body" => $text,
                            "mediaUrl" => $media						
                        ) 
              );
			  
    echo "WhatsApp Media Message Send...";
}

# Obtain the transferred information from Notecard via Notehub.io.
if(isset($_GET["results"]) && isset($_GET["temp"]) && isset($_GET["pH"]) && isset($_GET["TDS"])){
	$date = date("Y/m/d_h:i:s");
	// Send the received information via WhatsApp to the registered phone so as to notify the user.
	send_text_message($twilio, $account, "⏰ $date\n\n"
	                                 ."📌 Model Detection Results:\n🌱 "
									 .$_GET["results"]
									 ."\n\n📌 Water Quality:"
									 ."\n🌡️ Temperature: ".$_GET["temp"]
									 ."\n💧 pH: ". $_GET["pH"]
									 ."\n☁️ TDS: ".$_GET["TDS"]
	            );
	
	
}else{
	echo('{"body": "Waiting Data..."}');
}

# Obtain all image files transferred by Raspberry Pi in the detections folder.
function get_latest_detection_images($app){
	# Get all images in the detections folder.
	$images = glob('./detections/*.jpg');
    # Get the total image number.
	$total_detections = count($images);
	# If the detections folder contains images, sort the retrieved image files chronologically by date.
	$img_file_names = "";
	$img_queue = array();
	if(array_key_exists(0, $images)){
		usort($images, function($a, $b) {
			return filemtime($b) - filemtime($a);
		});
		# After sorting image files, save the retrieved image file names as a list and create the image queue by adding the given web application path to the file names.
		for($i=0; $i<$total_detections; $i++){
			$img_file_names .= "\n".$i.") ".basename($images[$i]);
			array_push($img_queue, $app.basename($images[$i]));
		}
	}
	# Return the generated image file data.
	return(array($total_detections, $img_file_names, $img_queue));
}

# If the verified phone transfers a message (command) to this webhook via WhatsApp:
if(isset($_POST['Body'])){
	switch($_POST['Body']){
		case "Latest Detection":
			# Get the total model detection image number, the generated image file name list, and the image queue. 
			list($total_detections, $img_file_names, $img_queue) = get_latest_detection_images("https://www.theamplituhedron.com/twilio_whatsapp_sender/detections/");
			# If the get_latest_detection_images function finds images in the detections folder, send the latest detection image to the verified phone via WhatsApp.
			if($total_detections > 0){
				send_media_message($twilio, $account, "🌐 Total Saved Images ➡️ ".$total_detections, $img_queue[0]);
			}else{
				# Otherwise, send a notification (text) message to the verified phone via WhatsApp.
				send_text_message($twilio, $account, "🌐 Total Saved Images ➡️ ".$total_detections."\n\n🖼️ No Detection Image Found!");
			}
			break;
		case "Oldest Detection":
			# Get the total model detection image number, the generated image file name list, and the image queue.
			list($total_detections, $img_file_names, $img_queue) = get_latest_detection_images("https://www.theamplituhedron.com/twilio_whatsapp_sender/detections/");
			# If the get_latest_detection_images function finds images in the detections folder, send the oldest detection image to the verified phone via WhatsApp.
			if($total_detections > 0){
				send_media_message($twilio, $account, "🌐 Total Saved Images ➡️ ".$total_detections, $img_queue[$total_detections-1]);
			}else{
				# Otherwise, send a notification (text) message to the verified phone via WhatsApp.
				send_text_message($twilio, $account, "🌐 Total Saved Images ➡️ ".$total_detections."\n\n🖼️ No Detection Image Found!");
			}
			break;
		case "Show List":
			# Get the total model detection image number, the generated image file name list, and the image queue.
			list($total_detections, $img_file_names, $img_queue) = get_latest_detection_images("https://www.theamplituhedron.com/twilio_whatsapp_sender/detections/");
			# If the get_latest_detection_images function finds images in the detections folder, send all retrieved image file names as a list to the verified phone via WhatsApp.
			if($total_detections > 0){
				send_text_message($twilio, $account, "🖼️ Image List:\n".$img_file_names);
			}else{
				# Otherwise, send a notification (text) message to the verified phone via WhatsApp.
				send_text_message($twilio, $account, "🌐 Total Saved Images ➡️ ".$total_detections."\n\n🖼️ No Detection Image Found!");
			}
            break;			
		default:
			if(strpos($_POST['Body'], "Display") !== 0){
				send_text_message($twilio, $account, "❌ Wrong command. Please enter one of these commands:\n\nLatest Detection\n\nOldest Detection\n\nShow List\n\nDisplay:<IMG_NUM>");
			}else{
				# Get the total model detection image number, the generated image file name list, and the image queue.
				list($total_detections, $img_file_names, $img_queue) = get_latest_detection_images("https://www.theamplituhedron.com/twilio_whatsapp_sender/detections/");
				# If the requested image exists in the detections folder, send the retrieved image with its file name to the verified phone via WhatsApp.
				$key = explode(":", $_POST['Body'].":none")[1];
				if(array_key_exists($key, $img_queue)){
					send_media_message($twilio, $account, "🖼️ ". explode("/", $img_queue[$key])[5], $img_queue[$key]);
				}else{
					send_text_message($twilio, $account, "🖼️ Image Not Found: ".$key.".jpg");
				}
			}
			break;
	}
}

?>