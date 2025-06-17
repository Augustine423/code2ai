import { useEffect, useRef, useState } from 'react';
import io from 'socket.io-client';
import './styles/droneFrame.css';

const config = {
  janusServer: 'ws://43.200.134.76:8188',
  socketServer: 'http://3.36.171.41:5000',
  streamId: 1234,
  secret: 'adminpwd',
  frameRate: 1,
};

const DroneFrameSender = () => {
  const [status, setStatus] = useState('Initializing...');
  const [error, setError] = useState('');
  const [framesSent, setFramesSent] = useState(0);
  const [lastAckTime, setLastAckTime] = useState('');
  const janusRef = useRef(null);
  const pluginRef = useRef(null);
  const remoteStreamRef = useRef(null);
  const videoRef = useRef(null);
  const socketRef = useRef(null);
  const frameIntervalRef = useRef(null);
  const captureCanvas = useRef(document.createElement('canvas'));
  const captureCtx = useRef(captureCanvas.current.getContext('2d'));
  const janusScriptRef = useRef(null);

  useEffect(() => {
    const adapterScript = document.createElement('script');
    adapterScript.src = '/adapter-latest.js';
    adapterScript.onload = loadJanus;
    document.body.appendChild(adapterScript);

    function loadJanus() {
      const janusScript = document.createElement('script');
      janusScript.src = '/janus.js';
      janusScript.onload = initializeJanus;
      document.body.appendChild(janusScript);
      janusScriptRef.current = janusScript;
    }

    function initializeJanus() {
      window.Janus.init({
        debug: 'all',
        callback: () => {
          if (!window.Janus.isWebrtcSupported()) {
            setError('WebRTC not supported by this browser');
            return;
          }

          janusRef.current = new window.Janus({
            server: config.janusServer,
            success: () => {
              setStatus('Connected to Janus server');
              attachToPlugin();
              setupSocket();
            },
            error: (err) => {
              setError(`Janus connection failed: ${err}`);
            },
            destroyed: () => {
              console.log('Janus destroyed');
            },
          });
        },
      });
    }

    function setupSocket() {
      const socket = io(config.socketServer, {
        transports: ['websocket'],
        reconnection: true,
        query: {
          user: 'source',
          did: 'drone_01',
        },
      });

      socket.on('connect', () => {
        setStatus('Socket.IO connected');
      });

      socket.on('connect_error', (err) => {
        setError(`Socket.IO error: ${err.message || err}`);
      });

      socket.on('server_response', (data) => {
        console.log('Server response:', data);
        if (data.status && data.received?.timestamp) {
          setLastAckTime(data.received.timestamp);
        }
      });

      socketRef.current = socket;
    }

    function attachToPlugin() {
      janusRef.current.attach({
        plugin: 'janus.plugin.streaming',
        opaqueId: `streaming-${config.streamId}-${window.Janus.randomString(12)}`,
        success: (pluginHandle) => {
          pluginRef.current = pluginHandle;
          setStatus('Plugin attached');
          startWatching();
        },
        error: (err) => {
          setError(`Plugin error: ${err}`);
        },
        onmessage: (msg, jsep) => {
          if (msg.error) {
            setError(msg.error);
            return;
          }
          if (jsep && pluginRef.current) {
            pluginRef.current.createAnswer({
              jsep,
              tracks: [{ type: 'video', recv: true }],
              success: (jsepAnswer) => {
                pluginRef.current.send({ message: { request: 'start' }, jsep: jsepAnswer });
              },
              error: (err) => {
                setError(`WebRTC error: ${err}`);
              },
            });
          }
        },
        onremotetrack: (track, trackMid, on) => {
          if (track.kind !== 'video') return;
          if (!remoteStreamRef.current) {
            remoteStreamRef.current = new MediaStream();
            if (videoRef.current) {
              videoRef.current.srcObject = remoteStreamRef.current;
            }
          }
          if (on) {
            remoteStreamRef.current.addTrack(track);
            setStatus('Receiving video stream...');
            if (!frameIntervalRef.current) {
              frameIntervalRef.current = setInterval(captureFrame, 500 / config.frameRate);
            }
          } else {
            remoteStreamRef.current.removeTrack(track);
            setStatus('Video track stopped');
          }
        },
        oncleanup: () => {
          setStatus('Stream cleaned up');
          clearInterval(frameIntervalRef.current);
          frameIntervalRef.current = null;
          remoteStreamRef.current = null;
          if (videoRef.current) videoRef.current.srcObject = null;
        },
      });
    }

    function startWatching() {
      pluginRef.current.send({
        message: {
          request: 'watch',
          id: config.streamId,
          secret: config.secret,
          offer_audio: false,
          offer_video: true,
        },
      });
      setStatus('Requesting stream...');
    }

    function captureFrame() {
        const video = videoRef.current;
        if (!video || !video.srcObject || video.videoWidth === 0) return;

        // Set canvas size to match video
        captureCanvas.current.width = video.videoWidth;
        captureCanvas.current.height = video.videoHeight;

        // Draw the current video frame to the canvas
        captureCtx.current.drawImage(video, 0, 0);

        // Convert canvas to JPEG Base64
        const base64Image = captureCanvas.current.toDataURL('image/jpeg', 0.5);

        // Construct the data object
        const data = {
            did: 'drone_01', // or 'drone_01' if needed
            img: base64Image,
            img_w: video.videoWidth,
            img_h: video.videoHeight,
            timestamp: new Date().toISOString(),
            message: `Data packet ${framesSent}`
        };

        // Emit if socket is connected
        if (socketRef.current?.connected) {
            socketRef.current.emit('source', data);
            setFramesSent((count) => count + 1);
        }
        }


    return () => {
      if (frameIntervalRef.current) clearInterval(frameIntervalRef.current);
      if (socketRef.current) socketRef.current.disconnect();
      if (janusRef.current) janusRef.current.destroy();
      if (videoRef.current) videoRef.current.srcObject = null;
      if (adapterScript) document.body.removeChild(adapterScript);
      if (janusScriptRef.current) document.body.removeChild(janusScriptRef.current);
    };
  }, []);

  return (
    <div className="relative min-h-screen text-white flex flex-col justify-center items-center gap-4 text-2xl font-mono font-bold overflow-hidden">
      <div className="particle-bg">
        {Array.from({ length: 200 }).map((_, i) => (
          <span
            key={i}
            className="particle"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 10}s`,
              animationDuration: `${10 + Math.random() * 10}s`,
            }}
          />
        ))}
      </div>

      <h3 className="animated-gradient-text">Drone Frame Sender</h3>
      <p>Status: {status}</p>
      {lastAckTime && <p>Last Ack: {lastAckTime}</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      <p>Frames Sent: {framesSent}</p>

      <div className="w-full h-full flex justify-center items-center shadow-lg shadow-red-500 p-5">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="w-1/2 h-1/3 shadow-xl shadow-blue-300"
        />
      </div>
    </div>
  );
};

export default DroneFrameSender;
