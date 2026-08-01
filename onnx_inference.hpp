#ifndef ONNX_INFERENCE_HPP
#define ONNX_INFERENCE_HPP

#include <onnxruntime_cxx_api.h>
#include <vector>
#include <string>
#include <iostream>
#include <map>

class ONNXModel {
private:
    Ort::Env env;
    Ort::Session session;
    Ort::AllocatorWithDefaultOptions allocator;
    
    std::vector<const char*> input_node_names;
    std::vector<const char*> output_node_names;
    std::vector<int64_t> input_node_dims;
    
    bool is_loaded = false;

public:
    ONNXModel(const std::string& model_path) 
        : env(ORT_LOGGING_LEVEL_WARNING, "AegisPQC"),
          session(nullptr)
    {
        try {
            Ort::SessionOptions session_options;
            session_options.SetIntraOpNumThreads(1);
            session_options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_EXTENDED);
            
            session = Ort::Session(env, model_path.c_str(), session_options);
            
            // For a simple scikit-learn random forest, there's usually 1 input and 2 outputs (labels, probabilities).
            Ort::TypeInfo type_info = session.GetInputTypeInfo(0);
            auto tensor_info = type_info.GetTensorTypeAndShapeInfo();
            input_node_dims = tensor_info.GetShape();
            
            // Override dynamic batch size if any
            if (input_node_dims[0] == -1) input_node_dims[0] = 1;

            input_node_names = {"float_input"};
            output_node_names = {"output_label", "output_probability"};
            
            is_loaded = true;
        } catch (const std::exception& e) {
            std::cerr << "Failed to load ONNX model from " << model_path << ": " << e.what() << std::endl;
        }
    }

    bool loaded() const { return is_loaded; }

    double predict(const std::vector<float>& features) {
        if (!is_loaded) return 0.0;

        auto memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
        
        Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
            memory_info, 
            const_cast<float*>(features.data()), 
            features.size(), 
            input_node_dims.data(), 
            input_node_dims.size()
        );
        
        auto output_tensors = session.Run(
            Ort::RunOptions{nullptr}, 
            input_node_names.data(), 
            &input_tensor, 
            1, 
            output_node_names.data(), 
            2
        );
        
        // Output 0 is the label (int64)
        // Output 1 is a sequence of maps (probability dictionary). skl2onnx exports it this way.
        // We will just return the label as double if parsing probabilities is too complex in C++.
        
        int64_t* label_ptr = output_tensors[0].GetTensorMutableData<int64_t>();
        return static_cast<double>(label_ptr[0]);
    }
};

#endif
