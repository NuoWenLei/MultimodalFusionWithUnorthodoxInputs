from imports import tf, Iterable, np, json, pd, date
from ConvLSTMCell import ConvLSTMCell

def create_conv_lstm_model(layer_units: Iterable,
input_shape: tuple,
filters: int,
output_size: int,
kernel_size: int,
name = "ConvLSTMModel"):
	input_layer = tf.keras.layers.Input(shape = input_shape)

	x = input_layer

	for i in range(len(layer_units) - 1):
		convLSTM_cell = ConvLSTMCell(
			units = layer_units[i],
			filters = filters,
			kernel_size = kernel_size,
			name = f"{name}_convLSTMCell_{i}"
		)

		x = tf.keras.layers.RNN(convLSTM_cell,
		return_sequences=True)(x)
	
	convLSTM_out_cell = ConvLSTMCell(
		units = layer_units[-1],
		filters = output_size,
		kernel_size = kernel_size,
		name = f"{name}_convLSTMCell_out"
	)

	out = tf.keras.layers.RNN(convLSTM_out_cell)(x)

	return tf.keras.models.Model(inputs = input_layer, outputs = out, name = name)
	
def load_sequential_data(maps_path: str,
metadata_path: str,
dataset_path: str,
image_x: int = 128,
image_y: int = 128,
num_days_per_sample: int = 7):
	with open(maps_path, "rb") as f:
		maps = np.load(f)

	with open(metadata_path, "r") as meta_json:
		metadata = json.load(meta_json)

	maps = tf.image.resize_with_pad(maps, image_x, image_y).numpy()

	df = pd.read_csv(dataset_path)

	dates = [date(int("20" + str(y)), m, d).strftime("%-m/%-d/%y") for y, m, d in metadata]
	dates_ordered = [date(int("20" + str(y)), m, d).strftime("%Y/%m/%d") for y, m, d in metadata]

	image_idx_dictionary = dict([(d, i) for i, d in enumerate(dates)])

	image_indices = []
	for i, row in df.iterrows():
		image_indices.append(image_idx_dictionary[row["date"]])

	df["image_index"] = image_indices

	date_df = pd.DataFrame({"date": dates, "date_actual": dates_ordered})

	date_df["image_index"] = date_df.index

	sorted_date_df = date_df.sort_values("date_actual", ascending = True)

	raw_y_list = []
	for d in sorted_date_df["date"].values:
		raw_y_list.append(df[df["date"] == d]["death_rate_from_population"].values)

	raw_X = maps[sorted_date_df["image_index"]]
	raw_metadata = sorted_date_df
	raw_y = np.array(raw_y_list)

	formatted_X_list = []
	formatted_y_list = []
	for i in range(raw_metadata.shape[0] - num_days_per_sample):
		formatted_X_list.append([n for n in range(i, i + num_days_per_sample)])


		formatted_y_list.append(raw_y[i + num_days_per_sample, ...])

	formatted_X = np.array(formatted_X_list)
	formatted_y = np.array(formatted_y_list)

	return formatted_X, formatted_y, raw_X

def create_flow(X_indices, y, batch_size, raw_X):
	index = 0
	while True:
		X_sample = []
		y_sample = []
		for _ in range(batch_size):
			X_sample.append(raw_X[X_indices[index, ...]])
			y_sample.append(y[index, ...])
			index += 1
			if index >= X_indices.shape[0]:
				index = 0
				p = np.random.permutation(y.shape[0])
				X_indices = X_indices[p]
				y = y[p]

		yield np.float32(X_sample), np.float32(y_sample)



	