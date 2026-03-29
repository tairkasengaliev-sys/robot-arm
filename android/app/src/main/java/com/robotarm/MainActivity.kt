package com.robotarm

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.SeekBar
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarker
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarkerResult
import com.robotarm.databinding.ActivityMainBinding
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private lateinit var cameraExecutor: ExecutorService
    private var handLandmarker: HandLandmarker? = null
    private var bluetoothAdapter: BluetoothAdapter? = null
    private var isConnected = false
    
    // Позиции сервоприводов
    private var servoPositions = intArrayOf(90, 90, 90, 90, 90, 90, 90, 90)
    
    companion object {
        private const val TAG = "RobotArm"
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = arrayOf(
            Manifest.permission.CAMERA,
            Manifest.permission.BLUETOOTH,
            Manifest.permission.BLUETOOTH_ADMIN,
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.BLUETOOTH_SCAN
        )
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        // Инициализация Bluetooth
        val bluetoothManager = getSystemService(BLUETOOTH_SERVICE) as BluetoothManager
        bluetoothAdapter = bluetoothManager.adapter
        
        // Инициализация MediaPipe Hand Landmarker
        initHandLandmarker()
        
        // Настройка слайдеров
        setupSliders()
        
        // Проверка разрешений
        if (allPermissionsGranted()) {
            startCamera()
        } else {
            ActivityCompat.requestPermissions(
                this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS
            )
        }
        
        cameraExecutor = Executors.newSingleThreadExecutor()
        
        // Кнопки управления
        binding.btnHome.setOnClickListener { sendCommand("HOME") }
        binding.btnGrip.setOnClickListener { sendCommand("GRIP") }
        binding.btnOpen.setOnClickListener { sendCommand("OPEN") }
        binding.btnConnect.setOnClickListener { toggleBluetooth() }
    }
    
    private fun initHandLandmarker() {
        val baseOptions = HandLandmarker.BaseOptions.builder()
            .setModelAssetPath("hand_landmarker.task")
            .build()
        
        val options = HandLandmarker.HandLandmarkerOptions.builder()
            .setBaseOptions(baseOptions)
            .setRunningMode(RunningMode.LIVE_STREAM)
            .setResultListener(this::processHandLandmarks)
            .build()
        
        try {
            handLandmarker = HandLandmarker.createFromOptions(this, options)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load model", e)
        }
    }
    
    private fun setupSliders() {
        val sliderNames = listOf(
            binding.sliderThumb, binding.sliderIndex, binding.sliderMiddle,
            binding.sliderRing, binding.sliderPinky, binding.sliderWrist,
            binding.sliderElbow, binding.sliderShoulder
        )
        
        val valueTexts = listOf(
            binding.valueThumb, binding.valueIndex, binding.valueMiddle,
            binding.valueRing, binding.valuePinky, binding.valueWrist,
            binding.valueElbow, binding.valueShoulder
        )
        
        for (i in sliderNames.indices) {
            sliderNames[i].value = 90f
            sliderNames[i].addOnChangeListener { slider, value, fromUser ->
                if (fromUser) {
                    servoPositions[i] = value.toInt()
                    valueTexts[i].text = "${value.toInt()}°"
                    sendServoPositions()
                }
            }
        }
    }
    
    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        
        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()
            
            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(binding.previewView.surfaceProvider)
            }
            
            val imageAnalyzer = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
                .also {
                    it.setAnalyzer(cameraExecutor) { imageProxy ->
                        processImageProxy(imageProxy)
                    }
                }
            
            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    this, CameraSelector.DEFAULT_BACK_CAMERA, preview, imageAnalyzer
                )
            } catch (e: Exception) {
                Log.e(TAG, "Camera binding failed", e)
            }
        }, ContextCompat.getMainExecutor(this))
    }
    
    private fun processImageProxy(imageProxy: ImageProxy) {
        handLandmarker?.let { landmarker ->
            val mpImage = imageProxy.toMediaPipeImage()
            landmarker.detectAsync(mpImage, imageProxy.imageInfo)
        }
        imageProxy.close()
    }
    
    private fun processHandLandmarks(result: HandLandmarkerResult, input: HandLandmarker.Input) {
        if (result.landmarks().isEmpty()) return
        
        val landmarks = result.landmarks()[0]
        
        // Расчёт углов сервоприводов из позиции руки
        val angles = calculateServoAngles(landmarks)
        
        // Обновление UI в главном потоке
        runOnUiThread {
            updateSliders(angles)
            sendServoPositions()
        }
    }
    
    private fun calculateServoAngles(landmarks: List<HandLandmarker.NormalizedLandmark>): IntArray {
        val angles = intArrayOf(90, 90, 90, 90, 90, 90, 90, 90)
        
        if (landmarks.size < 21) return angles
        
        // Извлечение关键点
        val wrist = landmarks[0]
        val thumbTip = landmarks[4]
        val indexTip = landmarks[8]
        val indexPip = landmarks[6]
        val middleTip = landmarks[12]
        val middlePip = landmarks[10]
        val ringTip = landmarks[16]
        val ringPip = landmarks[14]
        val pinkyTip = landmarks[20]
        val pinkyPip = landmarks[18]
        
        // Открытость пальцев (расстояние от кончика до сустава)
        fun fingerOpenness(tip: HandLandmarker.NormalizedLandmark, pip: HandLandmarker.NormalizedLandmark): Float {
            return kotlin.math.sqrt(
                kotlin.math.pow(tip.x() - pip.x(), 2f) + 
                kotlin.math.pow(tip.y() - pip.y(), 2f)
            )
        }
        
        val baseAngle = 30f
        val maxOpen = 0.15f
        
        // Пальцы
        angles[1] = (baseAngle + (fingerOpenness(indexTip, indexPip) / maxOpen).coerceAtMost(1f) * (180 - baseAngle)).toInt()
        angles[2] = (baseAngle + (fingerOpenness(middleTip, middlePip) / maxOpen).coerceAtMost(1f) * (180 - baseAngle)).toInt()
        angles[3] = (baseAngle + (fingerOpenness(ringTip, ringPip) / maxOpen).coerceAtMost(1f) * (180 - baseAngle)).toInt()
        angles[4] = (baseAngle + (fingerOpenness(pinkyTip, pinkyPip) / maxOpen).coerceAtMost(1f) * (180 - baseAngle)).toInt()
        
        // Большой палец
        val thumbOpen = kotlin.math.sqrt(
            kotlin.math.pow(thumbTip.x() - wrist.x(), 2f) + 
            kotlin.math.pow(thumbTip.y() - wrist.y(), 2f)
        )
        angles[0] = (45 + (thumbOpen / 0.2f).coerceAtMost(1f) * 90).toInt()
        
        // Запястье, локоть, плечо
        angles[5] = (90 + (wrist.y() - 0.5f) * 60).toInt().coerceIn(0, 180)
        angles[6] = (90 + (wrist.y() - 0.5f) * 40).toInt().coerceIn(0, 180)
        angles[7] = (90 + (wrist.x() - 0.5f) * 60).toInt().coerceIn(0, 180)
        
        return angles
    }
    
    private fun updateSliders(angles: IntArray) {
        val sliders = listOf(
            binding.sliderThumb, binding.sliderIndex, binding.sliderMiddle,
            binding.sliderRing, binding.sliderPinky, binding.sliderWrist,
            binding.sliderElbow, binding.sliderShoulder
        )
        
        val valueTexts = listOf(
            binding.valueThumb, binding.valueIndex, binding.valueMiddle,
            binding.valueRing, binding.valuePinky, binding.valueWrist,
            binding.valueElbow, binding.valueShoulder
        )
        
        for (i in angles.indices) {
            sliders[i].value = angles[i].toFloat()
            valueTexts[i].text = "${angles[i]}°"
            servoPositions[i] = angles[i]
        }
    }
    
    private fun sendServoPositions() {
        if (!isConnected) return
        
        val command = "SET:${servoPositions.joinToString(",")}"
        sendCommand(command)
    }
    
    private fun sendCommand(command: String) {
        if (!isConnected) {
            Log.d(TAG, "SIM: $command")
            return
        }
        
        // Отправка через Bluetooth (упрощённо)
        Log.d(TAG, "Sending: $command")
    }
    
    private fun toggleBluetooth() {
        if (bluetoothAdapter == null) {
            Toast.makeText(this, "Bluetooth not supported", Toast.LENGTH_SHORT).show()
            return
        }
        
        if (!isConnected) {
            // Запрос на подключение
            Toast.makeText(this, "Поиск устройств...", Toast.LENGTH_SHORT).show()
            // Здесь должен быть код сканирования и подключения
            isConnected = true
            binding.btnConnect.text = "Отключить"
            binding.statusText.text = "Статус: Подключено"
            Toast.makeText(this, "Подключено!", Toast.LENGTH_SHORT).show()
        } else {
            isConnected = false
            binding.btnConnect.text = "Подключить"
            binding.statusText.text = "Статус: Отключено"
        }
    }
    
    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(baseContext, it) == PackageManager.PERMISSION_GRANTED
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<String>, grantResults: IntArray
    ) {
        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            if (allPermissionsGranted()) {
                startCamera()
            } else {
                Toast.makeText(this, "Разрешения не предоставлены", Toast.LENGTH_SHORT).show()
                finish()
            }
        }
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
    }
    
    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
        handLandmarker?.close()
    }
}
