// const video = document.getElementById("camera");

// request camera access -- single camera direct stream
// if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
//     navigator.mediaDevices.getUserMedia({video:true})
//     .then(function(stream) {
//         video.srcObject = stream;
//     })
//     .catch(function(error) {
//         console.error("Error accessing the webcam: ", error);
//     });
// }
// else {
//     alert("webcam API not supported by your browser.")
// }

let index = 0;
let numCameras = null;
let videoDevices = null;

// multi-camera access:
// document.addEventListener("DOMContentLoaded", async function() {


//     try {
//         // request generic access for all devices
//         await navigator.mediaDevices.getUserMedia({video:true});

//         // get all media devices
//         const devices = await navigator.mediaDevices.enumerateDevices();

//         // keep only video inputs (cameras)
//         videoDevices = devices.filter(device => device.kind === 'videoinput');
//         const videoElement = document.getElementById('camera');

//         // check if no cameras present
//         if (videoDevices.length === 0) {
//             videoDevices = null;
//             // hide the literal video
//             // document.getElementById('camera').style.display = 'none';
//             videoElement.textContent = 'No cameras found..';
//             return;
//         }
//         numCameras = videoDevices.length;
//         // numCameras = 20; // hard coded value for testing


//         if (index >= numCameras) {
//             videoElement.textContent = "Camera index '" + index + "' not found!";
//             videoElement.srcObject = null;
//             return;
//         }

//         const selectedCamera = videoDevices[index];

//         const cameraStream = await navigator.mediaDevices.getUserMedia({
//             video: {
//                 deviceId: {exact: selectedCamera.deviceId}
//             }
//         });

//         videoElement.srcObject = cameraStream;
//         updatePageHeader();

//     }
//     catch (error) {
//         console.error("Error targeting selected camera index:", error);
//         // alert("Could not access the specified camera stream.");
//     }

// });


async function incrementIndex() {
    // // post request to update camera index (later tie the camera index to each specific user)
    // const dataUrlPath = '/api/security-camera/user/selected-camera-index'

    // const updateType = 'increment'

    // const response = await fetch(dataUrlPath, {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json'
    //     },
    //     body: JSON.stringify({message: updateType})
    // });

    // const result = await response.json();

    // index = result.newIndex; // update the local index with the updated index

    // // updatePageHeader();
    // return result.status;




}

async function decrementIndex() {
    // // post request to update camera index (later tie the camera index to each specific user)
    // const dataUrlPath = '/api/security-camera/user/selected-camera-index'

    // const updateType = 'decrement'

    // const response = await fetch(dataUrlPath, {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json'
    //     },
    //     body: JSON.stringify({message: updateType})
    // });

    // const result = await response.json();

    // index = result.newIndex; // update the local index with the updated index

    // // updatePageHeader();
    // return result.status;

}

function updatePageHeader() {
    const header = document.getElementById('page-header');

    header.textContent = "Camera " + (index+1) + " Video Feed" + " (" + numCameras + " total)";
}

// async function updateSelectedCameraStream() {
//     const videoElement = document.getElementById('camera');
//     const placeholderElement = document.getElementById("no-video-feed-placeholder");

//     if (videoDevices.length == 1) {
//         return;
//     }


//     if (index >= videoDevices.length || videoDevices == null) {
//         // videoElement.classList.remove("display");
//         videoElement.style.display = 'none';
//         placeholderElement.style.display = 'flex';
//         // videoElement.style.display = 'none';
//         // videoElement.textContent = "Camera index '" + index + "' not found!";
//         videoElement.srcObject = null;
//         return;
//     }
//     else {
//         // videoElement.classList.add("display");
//         videoElement.style.display = 'block';
//         placeholderElement.style.display = 'none';
//         console.log(videoDevices)
//         const selectedCamera = videoDevices[index];

//         const cameraStream = await navigator.mediaDevices.getUserMedia({
//             video: {
//                 deviceId: {exact: selectedCamera.deviceId}
//             }
//         });

//         videoElement.srcObject = cameraStream;
//     }


// }



// async function postCameraIndex() {
//     const dataUrlPath = '/api/security-camera/user/selected-camera-index'

//     const response = await fetch(dataUrlPath, {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json'
//         },
//         body: JSON.stringify({message: index})
//     });

//     const result = await response.json();
//     return result.status;
// }
