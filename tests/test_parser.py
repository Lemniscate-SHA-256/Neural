import os
import sys
import pytest
from lark import Lark, exceptions

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neural.parser.parser import ModelTransformer, create_parser, DSLValidationError, Severity

# Fixtures
@pytest.fixture
def layer_parser():
    return create_parser('layer')

@pytest.fixture
def network_parser():
    return create_parser('network')

@pytest.fixture
def research_parser():
    return create_parser('research')

@pytest.fixture
def define_parser():
    return create_parser('define')

@pytest.fixture
def transformer():
    return ModelTransformer()

# Layer Parsing Tests
@pytest.mark.parametrize(
    "layer_string, expected, test_id",
    [
        # Basic Layers
        ('Dense(128, "relu")', {'type': 'Dense', 'params': {'units': 128, 'activation': 'relu'}, 'sublayers': []}, "dense-relu"),
        ('Dense(units=256, activation="sigmoid")', {'type': 'Dense', 'params': {'units': 256, 'activation': 'sigmoid'}, 'sublayers': []}, "dense-sigmoid"),
        ('Conv2D(32, (3, 3), activation="relu")', {'type': 'Conv2D', 'params': {'filters': 32, 'kernel_size': (3, 3), 'activation': 'relu'}, 'sublayers': []}, "conv2d-relu"),
        ('Conv2D(filters=64, kernel_size=(5, 5), activation="tanh")', {'type': 'Conv2D', 'params': {'filters': 64, 'kernel_size': (5, 5), 'activation': 'tanh'}, 'sublayers': []}, "conv2d-tanh"),
        ('Conv2D(filters=32, kernel_size=3, activation="relu", padding="same")', {'type': 'Conv2D', 'params': {'filters': 32, 'kernel_size': 3, 'activation': 'relu', 'padding': 'same'}, 'sublayers': []}, "conv2d-padding"),
        ('MaxPooling2D(pool_size=(2, 2))', {'type': 'MaxPooling2D', 'params': {'pool_size': (2, 2)}, 'sublayers': []}, "maxpooling2d"),
        ('MaxPooling2D((3, 3), 2, "valid")', {'type': 'MaxPooling2D', 'params': {'pool_size': (3, 3), 'strides': 2, 'padding': 'valid'}, 'sublayers': []}, "maxpooling2d-strides"),
        ('Flatten()', {'type': 'Flatten', 'params': None, 'sublayers': []}, "flatten"),
        ('Dropout(0.5)', {'type': 'Dropout', 'params': {'rate': 0.5}, 'sublayers': []}, "dropout"),
        ('Dropout(rate=0.25)', {'type': 'Dropout', 'params': {'rate': 0.25}, 'sublayers': []}, "dropout-named"),
        ('BatchNormalization()', {'type': 'BatchNormalization', 'params': None, 'sublayers': []}, "batchnorm"),
        ('LayerNormalization()', {'type': 'LayerNormalization', 'params': None, 'sublayers': []}, "layernorm"),
        ('InstanceNormalization()', {'type': 'InstanceNormalization', 'params': None, 'sublayers': []}, "instancenorm"),
        ('GroupNormalization(groups=32)', {'type': 'GroupNormalization', 'params': {'groups': 32}, 'sublayers': []}, "groupnorm"),

        # Recurrent Layers
        ('LSTM(units=64)', {'type': 'LSTM', 'params': {'units': 64}, 'sublayers': []}, "lstm"),
        ('LSTM(units=128, return_sequences=true)', {'type': 'LSTM', 'params': {'units': 128, 'return_sequences': True}, 'sublayers': []}, "lstm-return"),
        ('GRU(units=32)', {'type': 'GRU', 'params': {'units': 32}, 'sublayers': []}, "gru"),
        ('SimpleRNN(units=16)', {'type': 'SimpleRNN', 'params': {'units': 16}, 'sublayers': []}, "simplernn"),
        ('LSTMCell(units=64)', {'type': 'LSTMCell', 'params': {'units': 64}, 'sublayers': []}, "lstmcell"),
        ('GRUCell(units=128)', {'type': 'GRUCell', 'params': {'units': 128}, 'sublayers': []}, "grucell"),
        ('SimpleRNNDropoutWrapper(units=16, dropout=0.3)', {'type': 'SimpleRNNDropoutWrapper', 'params': {'units': 16, 'dropout': 0.3}, 'sublayers': []}, "simplernn-dropout"),

        # Advanced Layers
        ('Attention()', {'type': 'Attention', 'params': None, 'sublayers': []}, "attention"),
        ('TransformerEncoder(num_heads=8, ff_dim=512)', {'type': 'TransformerEncoder', 'params': {'num_heads': 8, 'ff_dim': 512}, 'sublayers': []}, "transformer-encoder"),
        ('TransformerDecoder(num_heads=4, ff_dim=256)', {'type': 'TransformerDecoder', 'params': {'num_heads': 4, 'ff_dim': 256}, 'sublayers': []}, "transformer-decoder"),
        ('ResidualConnection()', {'type': 'ResidualConnection', 'params': {}, 'sublayers': []}, "residual"),
        ('Inception()', {'type': 'Inception', 'params': {}, 'sublayers': []}, "inception"),
        ('CapsuleLayer()', {'type': 'CapsuleLayer', 'params': {}, 'sublayers': []}, "capsule"),
        ('SqueezeExcitation()', {'type': 'SqueezeExcitation', 'params': {}, 'sublayers': []}, "squeeze"),
        ('GraphAttention(num_heads=4)', {'type': 'GraphAttention', 'params': {'num_heads': 4}, 'sublayers': []}, "graph-attention"),
        ('Embedding(input_dim=1000, output_dim=128)', {'type': 'Embedding', 'params': {'input_dim': 1000, 'output_dim': 128}, 'sublayers': []}, "embedding"),
        ('QuantumLayer()', {'type': 'QuantumLayer', 'params': {}, 'sublayers': []}, "quantum"),

        # Nested Layers
        (
            'TransformerEncoder(num_heads=8, ff_dim=512) { Dense(128, "relu") Dropout(0.3) }',
            {
                'type': 'TransformerEncoder', 'params': {'num_heads': 8, 'ff_dim': 512},
                'sublayers': [
                    {'type': 'Dense', 'params': {'units': 128, 'activation': 'relu'}, 'sublayers': []},
                    {'type': 'Dropout', 'params': {'rate': 0.3}, 'sublayers': []}
                ]
            },
            "transformer-nested"
        ),
        (
            'ResidualConnection() { Conv2D(32, (3,3)) BatchNormalization() }',
            {
                'type': 'ResidualConnection', 'params': {},
                'sublayers': [
                    {'type': 'Conv2D', 'params': {'filters': 32, 'kernel_size': (3, 3)}, 'sublayers': []},
                    {'type': 'BatchNormalization', 'params': None, 'sublayers': []}
                ]
            },
            "residual-nested"
        ),

        # Merge and Noise Layers
        ('Add()', {'type': 'Add', 'params': {}, 'sublayers': []}, "add"),
        ('Concatenate(axis=1)', {'type': 'Concatenate', 'params': {'axis': 1}, 'sublayers': []}, "concatenate"),
        ('GaussianNoise(stddev=0.1)', {'type': 'GaussianNoise', 'params': {'stddev': 0.1}, 'sublayers': []}, "gaussian-noise"),

        # HPO and Device
        (
            'Dense(HPO(choice(128, 256)))',
            {'type': 'Dense', 'params': {'units': {'hpo': {'type': 'categorical', 'values': [128, 256]}}}, 'sublayers': []},
            "dense-hpo-choice"
        ),
        ('Conv2D(64, (3,3)) @ "cuda:0"', {'type': 'Conv2D', 'params': {'filters': 64, 'kernel_size': (3, 3), 'device': 'cuda:0'}, 'sublayers': []}, "conv2d-device"),

        # Error Cases
        ('Dense(units=-1)', None, "dense-negative-units"),
        ('Dropout(1.5)', None, "dropout-high-rate-error"),
        ('TransformerEncoder(num_heads=0)', None, "transformer-zero-heads"),
        ('Conv2D(filters=32, kernel_size=(0, 0))', None, "conv2d-zero-kernel"),
        ('Dense(units="abc")', None, "dense-invalid-units"),
    ],
    ids=[
        "dense-relu", "dense-sigmoid", "conv2d-relu", "conv2d-tanh", "conv2d-padding", "maxpooling2d", "maxpooling2d-strides",
        "flatten", "dropout", "dropout-named", "batchnorm", "layernorm", "instancenorm", "groupnorm", "lstm", "lstm-return",
        "gru", "simplernn", "lstmcell", "grucell", "simplernn-dropout", "attention", "transformer-encoder", "transformer-decoder",
        "residual", "inception", "capsule", "squeeze", "graph-attention", "embedding", "quantum", "transformer-nested", "residual-nested",
        "add", "concatenate", "gaussian-noise", "dense-hpo-choice", "conv2d-device", "dense-negative-units", "dropout-high-rate-error",
        "transformer-zero-heads", "conv2d-zero-kernel", "dense-invalid-units"
    ]
)
def test_layer_parsing(layer_parser, transformer, layer_string, expected, test_id):
    if expected is None:
        with pytest.raises((exceptions.UnexpectedCharacters, exceptions.UnexpectedToken, DSLValidationError, exceptions.VisitError)):
            tree = layer_parser.parse(layer_string)
            transformer.transform(tree)
    else:
        tree = layer_parser.parse(layer_string)
        result = transformer.transform(tree)
        assert result == expected, f"Failed for {test_id}: expected {expected}, got {result}"

# Network Parsing Tests
@pytest.mark.parametrize(
    "network_string, expected, raises_error, test_id",
    [
        # Complex Network
        (
            """
            network TestModel {
                input: (None, 28, 28, 1)
                layers:
                    Conv2D(32, (3,3), "relu")
                    MaxPooling2D((2, 2))
                    Flatten()
                    Dense(128, "relu")
                    Output(10, "softmax")
                loss: "categorical_crossentropy"
                optimizer: "adam"
                train { epochs: 10 batch_size: 32 }
            }
            """,
            {
                'type': 'model', 'name': 'TestModel',
                'input': {'type': 'Input', 'shape': (None, 28, 28, 1)},
                'layers': [
                    {'type': 'Conv2D', 'params': {'filters': 32, 'kernel_size': (3, 3), 'activation': 'relu'}, 'sublayers': []},
                    {'type': 'MaxPooling2D', 'params': {'pool_size': (2, 2)}, 'sublayers': []},
                    {'type': 'Flatten', 'params': None, 'sublayers': []},
                    {'type': 'Dense', 'params': {'units': 128, 'activation': 'relu'}, 'sublayers': []},
                    {'type': 'Output', 'params': {'units': 10, 'activation': 'softmax'}, 'sublayers': []}
                ],
                'output_layer': {'type': 'Output', 'params': {'units': 10, 'activation': 'softmax'}, 'sublayers': []},
                'output_shape': 10,
                'loss': 'categorical_crossentropy',
                'optimizer': {'type': 'adam', 'params': {}},
                'training_config': {'epochs': 10, 'batch_size': 32},
                'execution_config': {'device': 'auto'},
                'framework': 'tensorflow',
                'shape_info': [],
                'warnings': []
            },
            False,
            "complex-model"
        ),

        # Nested Network (Vision Transformer-like)
        (
            """
            network ViT {
                input: (224, 224, 3)
                layers:
                    Conv2D(64, (7,7), strides=2) @ "cuda:0"
                    TransformerEncoder(num_heads=8, ff_dim=512) {
                        Conv2D(32, (3,3))
                        Dense(128)
                    } * 2
                    GlobalAveragePooling2D()
                    Dense(1000, "softmax")
                loss: "categorical_crossentropy"
                optimizer: "Adam(learning_rate=1e-4)"
            }
            """,
            {
                'type': 'model', 'name': 'ViT',
                'input': {'type': 'Input', 'shape': (224, 224, 3)},
                'layers': [
                    {'type': 'Conv2D', 'params': {'filters': 64, 'kernel_size': (7, 7), 'strides': 2, 'device': 'cuda:0'}, 'sublayers': []},
                    {
                        'type': 'TransformerEncoder', 'params': {'num_heads': 8, 'ff_dim': 512},
                        'sublayers': [
                            {'type': 'Conv2D', 'params': {'filters': 32, 'kernel_size': (3, 3)}, 'sublayers': []},
                            {'type': 'Dense', 'params': {'units': 128}, 'sublayers': []}
                        ]
                    },
                    {
                        'type': 'TransformerEncoder', 'params': {'num_heads': 8, 'ff_dim': 512},
                        'sublayers': [
                            {'type': 'Conv2D', 'params': {'filters': 32, 'kernel_size': (3, 3)}, 'sublayers': []},
                            {'type': 'Dense', 'params': {'units': 128}, 'sublayers': []}
                        ]
                    },
                    {'type': 'GlobalAveragePooling2D', 'params': {}, 'sublayers': []},
                    {'type': 'Dense', 'params': {'units': 1000, 'activation': 'softmax'}, 'sublayers': []}
                ],
                'output_layer': {'type': 'Dense', 'params': {'units': 1000, 'activation': 'softmax'}, 'sublayers': []},
                'output_shape': 1000,
                'loss': 'categorical_crossentropy',
                'optimizer': {'type': 'Adam', 'params': {'learning_rate': 0.0001}},
                'training_config': None,
                'execution_config': {'device': 'auto'},
                'framework': 'tensorflow',
                'shape_info': [],
                'warnings': []
            },
            False,
            "nested-vit"
        ),

        # HPO Network
        (
            """
            network HPOExample {
                input: (10,)
                layers:
                    Dense(HPO(choice(128, 256)))
                    Dropout(HPO(range(0.3, 0.7, step=0.1)))
                loss: "mse"
                optimizer: "Adam(learning_rate=HPO(log_range(1e-4, 1e-2)))"
                train { search_method: "bayesian" }
            }
            """,
            {
                'type': 'model', 'name': 'HPOExample',
                'input': {'type': 'Input', 'shape': (10,)},
                'layers': [
                    {'type': 'Dense', 'params': {'units': {'hpo': {'type': 'categorical', 'values': [128, 256]}}}, 'sublayers': []},
                    {'type': 'Dropout', 'params': {'rate': {'hpo': {'type': 'range', 'start': 0.3, 'end': 0.7, 'step': 0.1}}}, 'sublayers': []}
                ],
                'output_layer': None,
                'output_shape': None,
                'loss': 'mse',
                'optimizer': {'type': 'Adam', 'params': {'learning_rate': {'hpo': {'type': 'log_range', 'low': 0.0001, 'high': 0.01}}}},
                'training_config': {'search_method': 'bayesian'},
                'execution_config': {'device': 'auto'},
                'framework': 'tensorflow',
                'shape_info': [],
                'warnings': []
            },
            False,
            "hpo-example"
        ),

        # Error Cases
        (
            """
            network InvalidDevice {
                input: (10,)
                layers:
                    Dense(5) @ "npu"
                loss: "mse"
                optimizer: "sgd"
            }
            """,
            None,
            True,
            "invalid-device"
        ),
        (
            """
            network MissingLayers {
                input: (10,)
                loss: "mse"
                optimizer: "sgd"
            }
            """,
            None,
            True,
            "missing-layers"
        ),
    ],
    ids=["complex-model", "nested-vit", "hpo-example", "invalid-device", "missing-layers"]
)
def test_network_parsing(network_parser, transformer, network_string, expected, raises_error, test_id):
    if raises_error:
        with pytest.raises((exceptions.UnexpectedCharacters, exceptions.UnexpectedToken, DSLValidationError, exceptions.VisitError)):
            transformer.parse_network(network_string)
    else:
        result = transformer.parse_network(network_string)
        assert result == expected, f"Failed for {test_id}: expected {expected}, got {result}"

# Research Parsing Tests
@pytest.mark.parametrize(
    "research_string, expected_name, expected_metrics, expected_references, test_id",
    [
        (
            """
            research ResearchStudy {
                metrics {
                    accuracy: 0.95
                    loss: 0.05
                }
                references {
                    paper: "Paper Title 1"
                    paper: "Another Great Paper"
                }
            }
            """,
            "ResearchStudy", {'accuracy': 0.95, 'loss': 0.05}, ["Paper Title 1", "Another Great Paper"],
            "complete-research"
        ),
        (
            """
            research {
                metrics {
                    precision: 0.8
                    recall: 0.9
                }
            }
            """,
            None, {'precision': 0.8, 'recall': 0.9}, [],
            "no-name-no-ref"
        ),
        (
            """
            research InvalidMetrics {
                metrics {
                    accuracy: "high"
                }
            }
            """,
            None, None, None,
            "invalid-metrics"
        ),
    ],
    ids=["complete-research", "no-name-no-ref", "invalid-metrics"]
)
def test_research_parsing(research_parser, transformer, research_string, expected_name, expected_metrics, expected_references, test_id):
    if expected_metrics is None:
        with pytest.raises((exceptions.UnexpectedCharacters, exceptions.UnexpectedToken, DSLValidationError)):
            tree = research_parser.parse(research_string)
            transformer.transform(tree)
    else:
        tree = research_parser.parse(research_string)
        result = transformer.transform(tree)
        assert result['type'] == 'Research'
        assert result['name'] == expected_name
        assert result.get('params', {}).get('metrics', {}) == expected_metrics
        assert result.get('params', {}).get('references', []) == expected_references

# Macro Parsing Tests
@pytest.mark.parametrize(
    "config, expected_definition, expected_reference, raises_error, test_id",
    [
        (
            """
            define MyDense {
                Dense(128, "relu")
            }
            """,
            [{'type': 'Dense', 'params': {'units': 128, 'activation': 'relu'}, 'sublayers': []}],
            {'type': 'MyDense', 'params': {}, 'sublayers': []},
            False,
            "macro-basic"
        ),
        (
            """
            define ResBlock {
                Conv2D(64, (3,3))
                BatchNormalization()
                ResidualConnection() {
                    Dense(128)
                    Dropout(0.3)
                }
            }
            """,
            [
                {'type': 'Conv2D', 'params': {'filters': 64, 'kernel_size': (3, 3)}, 'sublayers': []},
                {'type': 'BatchNormalization', 'params': None, 'sublayers': []},
                {
                    'type': 'ResidualConnection', 'params': {},
                    'sublayers': [
                        {'type': 'Dense', 'params': {'units': 128}, 'sublayers': []},
                        {'type': 'Dropout', 'params': {'rate': 0.3}, 'sublayers': []}
                    ]
                }
            ],
            {'type': 'ResBlock', 'params': {}, 'sublayers': []},
            False,
            "macro-nested"
        ),
        (
            "UndefinedMacro()",
            None,
            None,
            True,
            "macro-undefined"
        ),
    ],
    ids=["macro-basic", "macro-nested", "macro-undefined"]
)
def test_macro_parsing(define_parser, layer_parser, transformer, config, expected_definition, expected_reference, raises_error, test_id):
    if raises_error:
        with pytest.raises((exceptions.UnexpectedCharacters, exceptions.UnexpectedToken, DSLValidationError)):
            tree = layer_parser.parse(config)
            transformer.transform(tree)
    else:
        define_tree = define_parser.parse(config)
        definition_result = transformer.transform(define_tree)
        assert definition_result == expected_definition, f"Definition mismatch in {test_id}"
        
        ref_string = f"{config.split()[1]}()"
        ref_tree = layer_parser.parse(ref_string)
        ref_result = transformer.transform(ref_tree)
        assert ref_result == expected_reference, f"Reference mismatch in {test_id}"

# Wrapper Parsing Tests
@pytest.mark.parametrize(
    "wrapper_string, expected, test_id",
    [
        (
            'TimeDistributed(Dense(128, "relu"), dropout=0.5)',
            {'type': 'TimeDistributed(Dense)', 'params': {'units': 128, 'activation': 'relu', 'dropout': 0.5}, 'sublayers': []},
            "timedistributed-dense"
        ),
        (
            'TimeDistributed(Conv2D(32, (3, 3))) { Dropout(0.2) }',
            {
                'type': 'TimeDistributed(Conv2D)', 'params': {'filters': 32, 'kernel_size': (3, 3)},
                'sublayers': [{'type': 'Dropout', 'params': {'rate': 0.2}, 'sublayers': []}]
            },
            "timedistributed-conv2d-nested"
        ),
        (
            'TimeDistributed(Dropout("invalid"))',
            None,
            "timedistributed-invalid"
        ),
    ],
    ids=["timedistributed-dense", "timedistributed-conv2d-nested", "timedistributed-invalid"]
)
def test_wrapper_parsing(layer_parser, transformer, wrapper_string, expected, test_id):
    if expected is None:
        with pytest.raises((exceptions.UnexpectedCharacters, exceptions.UnexpectedToken, DSLValidationError)):
            tree = layer_parser.parse(wrapper_string)
            transformer.transform(tree)
    else:
        tree = layer_parser.parse(wrapper_string)
        result = transformer.transform(tree)
        assert result == expected, f"Failed for {test_id}"

# Lambda Parsing Tests
@pytest.mark.parametrize(
    "lambda_string, expected, test_id",
    [
        (
            'Lambda("x: x * 2")',
            {'type': 'Lambda', 'params': {'function': 'x: x * 2'}, 'sublayers': []},
            "lambda-multiply"
        ),
        (
            'Lambda("lambda x: x + 1")',
            {'type': 'Lambda', 'params': {'function': 'lambda x: x + 1'}, 'sublayers': []},
            "lambda-add"
        ),
        (
            'Lambda(123)',
            None,
            "lambda-invalid"
        ),
    ],
    ids=["lambda-multiply", "lambda-add", "lambda-invalid"]
)
def test_lambda_parsing(layer_parser, transformer, lambda_string, expected, test_id):
    if expected is None:
        with pytest.raises((exceptions.UnexpectedCharacters, exceptions.UnexpectedToken, DSLValidationError)):
            tree = layer_parser.parse(lambda_string)
            transformer.transform(tree)
    else:
        tree = layer_parser.parse(lambda_string)
        result = transformer.transform(tree)
        assert result == expected, f"Failed for {test_id}"

# Custom Shape Parsing Tests
@pytest.mark.parametrize(
    "custom_shape_string, expected, test_id",
    [
        (
            'CustomShape(MyLayer, (32, 32))',
            {"type": "CustomShape", "layer": "MyLayer", "custom_dims": (32, 32)},
            "custom-shape-normal"
        ),
        (
            'CustomShape(MyLayer, (-1, 32))',
            None,
            "custom-shape-negative"
        ),
    ],
    ids=["custom-shape-normal", "custom-shape-negative"]
)
def test_custom_shape_parsing(layer_parser, transformer, custom_shape_string, expected, test_id):
    if expected is None:
        with pytest.raises((exceptions.UnexpectedCharacters, exceptions.UnexpectedToken, DSLValidationError)):
            tree = layer_parser.parse(custom_shape_string)
            transformer.transform(tree)
    else:
        tree = layer_parser.parse(custom_shape_string)
        result = transformer.transform(tree)
        assert result == expected, f"Failed for {test_id}"

# Comment Parsing Tests
@pytest.mark.parametrize(
    "comment_string, expected, test_id",
    [
        (
            'Dense(128, "relu")  # Dense layer with ReLU activation',
            {'type': 'Dense', 'params': {'units': 128, 'activation': 'relu'}, 'sublayers': []},
            "dense-with-comment"
        ),
        (
            'Dropout(0.5)  # Dropout layer',
            {'type': 'Dropout', 'params': {'rate': 0.5}, 'sublayers': []},
            "dropout-with-comment"
        ),
        (
            'Conv2D(32, (3, 3)) # Multi-line\n# comment',
            {'type': 'Conv2D', 'params': {'filters': 32, 'kernel_size': (3, 3)}, 'sublayers': []},
            "conv2d-multi-comment"
        ),
    ],
    ids=["dense-with-comment", "dropout-with-comment", "conv2d-multi-comment"]
)
def test_comment_parsing(layer_parser, transformer, comment_string, expected, test_id):
    tree = layer_parser.parse(comment_string)
    result = transformer.transform(tree)
    assert result == expected, f"Failed for {test_id}"

# Severity Level and Warning Tests
@pytest.mark.parametrize(
    "layer_string, expected_result, expected_warnings, raises_error, test_id",
    [
        (
            'Dropout(1.1)',
            {'type': 'Dropout', 'params': {'rate': 1.1}, 'sublayers': []},
            [{'warning': 'Dropout rate should be between 0 and 1, got 1.1', 'line': 1, 'column': None}],
            False,
            "dropout-high-rate-warning"
        ),
        (
            'Dropout(-0.1)',
            None,
            [],
            True,
            "dropout-negative-rate-error"
        ),
        (
            'Dense(256.0, "relu")',
            {'type': 'Dense', 'params': {'units': 256, 'activation': 'relu'}, 'sublayers': []},
            [{'warning': 'Implicit conversion of 256.0 to integer 256', 'line': 1, 'column': None}],
            False,
            "dense-type-coercion-info"
        ),
        (
            'Conv2D(32, (3,3)) @ "npu"',  # Assuming validation for valid devices: ["cpu", "cuda", "tpu"]
            None,
            [],
            True,
            "invalid-device-critical"
        ),
    ],
    ids=["dropout-high-rate-warning", "dropout-negative-rate-error", "dense-type-coercion-info", "invalid-device-critical"]
)
def test_severity_level_parsing(layer_parser, transformer, layer_string, expected_result, expected_warnings, raises_error, test_id):
    if raises_error:
        with pytest.raises((exceptions.UnexpectedCharacters, exceptions.UnexpectedToken, DSLValidationError, exceptions.VisitError)):
            tree = layer_parser.parse(layer_string)
            transformer.transform(tree)
    else:
        tree = layer_parser.parse(layer_string)
        result = transformer.transform(tree)
        assert result == expected_result, f"Result mismatch for {test_id}"
        # Note: Warnings are currently logged, not returned. If modified to return, uncomment:
        # assert 'warnings' in result and result['warnings'] == expected_warnings, f"Warnings mismatch for {test_id}"

# Validation Rules Tests
@pytest.mark.parametrize(
    "network_string, expected_error_msg, test_id",
    [
        (
            """
            network InvalidSplit {
                input: (10,)
                layers: Dense(5)
                loss: "mse"
                optimizer: "sgd"
                train { validation_split: 1.5 }
            }
            """,
            "validation_split must be between 0 and 1, got 1.5",
            "invalid-validation-split"
        ),
        (
            """
            network MissingUnits {
                input: (10,)
                layers: Dense()
                loss: "mse"
                optimizer: "sgd"
            }
            """,
            "Dense layer requires 'units' parameter",
            "missing-units"
        ),
        (
            """
            network NegativeFilters {
                input: (28, 28, 1)
                layers: Conv2D(-32, (3,3))
                loss: "mse"
                optimizer: "sgd"
            }
            """,
            "Conv2D filters must be a positive integer, got -32",
            "negative-filters"
        ),
    ],
    ids=["invalid-validation-split", "missing-units", "negative-filters"]
)
def test_validation_rules(network_parser, transformer, network_string, expected_error_msg, test_id):
    with pytest.raises(DSLValidationError) as exc_info:
        transformer.parse_network(network_string)
    assert expected_error_msg in str(exc_info.value), f"Error message mismatch for {test_id}"
    def test_grammar_token_definitions():
        """Test that grammar token definitions are correct and complete."""
        parser = create_parser()
        lexer_conf = parser.parser.lexer_conf
        
        # Test all expected token patterns
        token_patterns = {
            'TRANSFORMER': r'transformer',
            'LSTM': r'lstm',
            'GRU': r'gru',
            'DENSE': r'dense',
            'CONV2D': r'conv2d',
            'NAME': r'[a-zA-Z_][a-zA-Z0-9_]*',
            'NUMBER': r'[+-]?([0-9]*[.])?[0-9]+',
            'STRING': r'\"[^"]+\"|\'[^\']+\'',
            'CUSTOM_LAYER': r'[A-Z][a-zA-Z0-9]*Layer'
        }
        
        for token_name, pattern in token_patterns.items():
            matching_token = next((t for t in lexer_conf.terminals if t.name == token_name), None)
            assert matching_token is not None, f"Token {token_name} not found in grammar"
            assert str(matching_token.pattern) == pattern, f"Unexpected pattern for {token_name}"

    def test_rule_dependencies():
        """Test that grammar rules have correct dependencies."""
        parser = create_parser()
        rules = {rule.origin.name: rule for rule in parser.grammar.rules}
        
        # Check essential rule dependencies
        dependencies = {
            'network': ['input_layer', 'layers', 'loss', 'optimizer'],
            'layer': ['conv', 'pooling', 'dropout', 'flatten', 'dense'],
            'conv': ['conv1d', 'conv2d', 'conv3d'],
            'pooling': ['max_pooling', 'average_pooling', 'global_pooling']
        }
        
        for rule_name, required_deps in dependencies.items():
            assert rule_name in rules, f"Missing rule: {rule_name}"
            rule = rules[rule_name]
            for dep in required_deps:
                assert dep in str(rule), f"Rule {rule_name} missing dependency {dep}"

    @pytest.mark.parametrize("rule_name,valid_inputs", [
        ('NAME', ['valid_name', '_valid_name', 'ValidName123']),
        ('NUMBER', ['123', '-123', '123.456', '-123.456']),
        ('STRING', ['"valid string"', "'valid string'"]),
        ('CUSTOM_LAYER', ['CustomLayer', 'MyTestLayer', 'ConvLayer'])
    ])
    def test_token_patterns(rule_name, valid_inputs):
        """Test that token patterns match expected inputs."""
        parser = create_parser()
        for input_str in valid_inputs:
            try:
                result = parser.parse(f"network TestNet {{ input: (1,1) layers: {input_str} }}")
                assert result is not None
            except Exception as e:
                pytest.fail(f"Failed to parse {rule_name} with input {input_str}: {str(e)}")

    def test_rule_precedence():
        """Test that grammar rules have correct precedence."""
        parser = create_parser()
        test_cases = [
            ('dense_basic', 'Dense(10)'),
            ('dense_params', 'Dense(units=10, activation="relu")'),
            ('conv_basic', 'Conv2D(32, (3,3))'),
            ('conv_params', 'Conv2D(filters=32, kernel_size=(3,3))'),
            ('nested_block', 'Transformer() { Dense(10) }')
        ]
        
        for test_id, test_input in test_cases:
            try:
                result = parser.parse(f"network TestNet {{ input: (1,1) layers: {test_input} }}")
                assert result is not None, f"Failed to parse {test_id}"
            except Exception as e:
                pytest.fail(f"Failed to parse {test_id}: {str(e)}")

    def test_grammar_ambiguity():
        """Test that grammar doesn't have ambiguous rules."""
        parser = create_parser()
        test_cases = [
            ('params_order1', 'Dense(10, "relu")'),
            ('params_order2', 'Dense(units=10, activation="relu")'),
            ('mixed_params', 'Conv2D(32, kernel_size=(3,3))'),
            ('nested_params', 'Transformer(num_heads=8) { Dense(10) }')
        ]
        
        for test_id, test_input in test_cases:
            try:
                results = list(parser.parse_interactive(f"network TestNet {{ input: (1,1) layers: {test_input} }}"))
                assert len(results) == 1, f"Ambiguous parsing for {test_id}"
            except Exception as e:
                pytest.fail(f"Failed to parse {test_id}: {str(e)}")

    def test_error_recovery():
        """Test parser's error recovery capabilities."""
        parser = create_parser()
        test_cases = [
            ('missing_param', 'Dense()', DSLValidationError),
            ('invalid_param', 'Dense("invalid")', DSLValidationError),
            ('incomplete_block', 'Transformer() {', lark.UnexpectedToken),
            ('missing_close', 'network Test { input: (1,1) layers: Dense(10)', lark.UnexpectedEOF)
        ]
        
        for test_id, test_input, expected_error in test_cases:
            with pytest.raises(expected_error):
                parser.parse(test_input)

    @pytest.mark.parametrize("test_input,expected_error", [
        ('network Test { input: (1,1) layers: Dense(units=-10) }', 'units must be positive'),
        ('network Test { input: (1,1) layers: Dropout(rate=1.5) }', 'rate must be between 0 and 1'),
        ('network Test { input: (1,1) layers: Conv2D(filters=0) }', 'filters must be positive')
    ])
    def test_semantic_validation(test_input, expected_error):
        """Test semantic validation of parsed values."""
        parser = create_parser()
        with pytest.raises(DSLValidationError) as exc_info:
            parser.parse(test_input)
        assert expected_error in str(exc_info.value)

    def test_grammar_completeness():
        """Test that grammar covers all required language features."""
        parser = create_parser()
        # Additional Layer Parsing Tests
        @pytest.mark.parametrize(
            "layer_string, expected, test_id",
            [
                # Extended Basic Layer Tests
                ('Dense(64, activation="tanh")', 
                 {'type': 'Dense', 'params': {'units': 64, 'activation': 'tanh'}, 'sublayers': []}, 
                 "dense-tanh"),
                
                # Multiple Parameter Tests
                ('Conv2D(32, (3,3), strides=(2,2), padding="same", activation="relu")',
                 {'type': 'Conv2D', 'params': {
                     'filters': 32, 
                     'kernel_size': (3,3),
                     'strides': (2,2),
                     'padding': 'same',
                     'activation': 'relu'
                 }, 'sublayers': []},
                 "conv2d-multiple-params"),
                
                # Layer with Mixed Parameter Styles
                ('LSTM(128, return_sequences=true, dropout=0.2)',
                 {'type': 'LSTM', 'params': {
                     'units': 128,
                     'return_sequences': True,
                     'dropout': 0.2
                 }, 'sublayers': []},
                 "lstm-mixed-params"),
                
                # Nested Layer with Complex Configuration
                ('''TransformerEncoder(num_heads=8, ff_dim=256) {
                    LayerNormalization()
                    Dense(64, "relu")
                    Dropout(0.1)
                }''',
                 {'type': 'TransformerEncoder', 
                  'params': {'num_heads': 8, 'ff_dim': 256},
                  'sublayers': [
                      {'type': 'LayerNormalization', 'params': None, 'sublayers': []},
                      {'type': 'Dense', 'params': {'units': 64, 'activation': 'relu'}, 'sublayers': []},
                      {'type': 'Dropout', 'params': {'rate': 0.1}, 'sublayers': []}
                  ]},
                 "transformer-complex"),
                
                # Edge Cases
                ('Dense(0)', None, "dense-zero-units"),
                ('Conv2D(32, (0,0))', None, "conv2d-zero-kernel"),
                ('Dropout(2.0)', None, "dropout-invalid-rate"),
                ('LSTM(units=-1)', None, "lstm-negative-units"),
                
                # Device Specification Tests
                ('Dense(128) @ "cpu"',
                 {'type': 'Dense', 'params': {'units': 128, 'device': 'cpu'}, 'sublayers': []},
                 "dense-cpu-device"),
                ('Dense(128) @ "invalid_device"', None, "dense-invalid-device"),
                
                # Custom Layer Tests
                ('CustomTestLayer(param1=10, param2="test")',
                 {'type': 'CustomTestLayer', 'params': {'param1': 10, 'param2': 'test'}, 'sublayers': []},
                 "custom-layer-basic"),
                
                # Activation Layer Tests
                ('Activation("leaky_relu", alpha=0.1)',
                 {'type': 'Activation', 'params': {'function': 'leaky_relu', 'alpha': 0.1}, 'sublayers': []},
                 "activation-with-params"),
                
                # Layer with HPO Parameters
                ('Dense(HPO(choice(32, 64, 128)), activation=HPO(choice("relu", "tanh")))',
                 {'type': 'Dense', 
                  'params': {
                      'units': {'hpo': {'type': 'categorical', 'values': [32, 64, 128]}},
                      'activation': {'hpo': {'type': 'categorical', 'values': ['relu', 'tanh']}}
                  }, 'sublayers': []},
                 "dense-hpo-multiple"),
            ]
        )
        def test_extended_layer_parsing(layer_parser, transformer, layer_string, expected, test_id):
            """Test parsing of various layer configurations with extended test cases."""
            if expected is None:
                with pytest.raises((exceptions.UnexpectedCharacters, 
                                  exceptions.UnexpectedToken, 
                                  DSLValidationError)):
                    tree = layer_parser.parse(layer_string)
                    transformer.transform(tree)
            else:
                tree = layer_parser.parse(layer_string)
                result = transformer.transform(tree)
                assert result == expected, f"Failed for {test_id}: expected {expected}, got {result}"

        @pytest.mark.parametrize(
            "layer_string, validation_error_msg, test_id",
            [
                ('Dense(units="invalid")', "units must be a number", "dense-invalid-units-type"),
                ('Conv2D(filters=-5, kernel_size=(3,3))', "filters must be positive", "conv2d-negative-filters"),
                ('LSTM(units=0, return_sequences=true)', "units must be positive", "lstm-zero-units"),
                ('Dropout(rate=1.5)', "rate must be between 0 and 1", "dropout-high-rate"),
                ('BatchNormalization(momentum=2.0)', "momentum must be between 0 and 1", "batchnorm-invalid-momentum"),
                ('Dense(128) @ "unknown_device"', "Invalid device specification", "invalid-device-spec"),
                ('Conv2D(32, (-1,-1))', "kernel size must be positive", "conv2d-negative-kernel"),
                ('MaxPooling2D(pool_size=(0,0))', "pool size must be positive", "maxpool-zero-size"),
            ]
        )
        def test_layer_validation_errors(layer_parser, transformer, layer_string, validation_error_msg, test_id):
            """Test validation error messages for invalid layer configurations."""
            with pytest.raises(DSLValidationError) as exc_info:
                tree = layer_parser.parse(layer_string)
                transformer.transform(tree)
            assert validation_error_msg in str(exc_info.value), f"Error message mismatch for {test_id}"