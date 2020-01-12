import numpy as np 
import json 
from scipy.spatial.transform import Rotation as R
import tensorflow as tf
with open('/home/jules/Documents/recvis-project/refined/backflip_a.json') as f:
    data = json.load(f)

keys = [int(k) for k in data]
keys = sorted(keys)

def batch_skew(vec, batch_size=None):
    """
    vec is N x 3, batch_size is int

    returns N x 3 x 3. Skew_sym version of each matrix.
    """
    with tf.name_scope("batch_skew", values=[vec]):
        if batch_size is None:
            batch_size = vec.shape.as_list()[0]
        col_inds = tf.constant([1, 2, 3, 5, 6, 7])
        indices = tf.reshape(
            tf.reshape(tf.range(0, batch_size) * 9, [-1, 1]) + col_inds,
            [-1, 1])
        updates = tf.reshape(
            tf.stack(
                [
                    -vec[:, 2], vec[:, 1], vec[:, 2], -vec[:, 0], -vec[:, 1],
                    vec[:, 0]
                ],
                axis=1), [-1])
        out_shape = [batch_size * 9]
        res = tf.scatter_nd(indices, updates, out_shape)
        res = tf.reshape(res, [batch_size, 3, 3])

        return res


def batch_rodrigues(theta, name=None):
    """
    Theta is N x 3
    """
    with tf.name_scope(name, "batch_rodrigues", values=[theta]):
        batch_size = theta.shape.as_list()[0]

        # angle = tf.norm(theta, axis=1)
        # r = tf.expand_dims(tf.div(theta, tf.expand_dims(angle + 1e-8, -1)), -1)
        # angle = tf.expand_dims(tf.norm(theta, axis=1) + 1e-8, -1)
        angle = tf.expand_dims(tf.norm(theta + 1e-8, axis=1), -1)
        r = tf.expand_dims(tf.div(theta, angle), -1)

        angle = tf.expand_dims(angle, -1)
        cos = tf.cos(angle)
        sin = tf.sin(angle)

        outer = tf.matmul(r, r, transpose_b=True, name="outer")

        eyes = tf.tile(tf.expand_dims(tf.eye(3), 0), [batch_size, 1, 1])
        R = cos * eyes + (1 - cos) * outer + sin * batch_skew(
            r, batch_size=batch_size)
        return R

theta_names = [
                'Left_Hip',
                'Right_Hip', 
                'Waist', 
                'Left_Knee', 
                'Right_Knee',
                'Upper_Waist', 
                'Left_Ankle', 
                'Right_Ankle', 
                'Chest',
                'Left_Toe', 
                'Right_Toe', 
                'Base_Neck', 
                'Left_Shoulder',
                'Right_Shoulder', 
                'Upper_Neck', 
                'Left_Arm', 
                'Right_Arm',
                'Left_Elbow', 
                'Right_Elbow', 
                'Left_Wrist', 
                'Right_Wrist',
                'Left_Finger', 
                'Right_Finger'
            ]

theta_wanted = [
                'Chest',
                'Upper_Neck', 
                'Right_Hip', 
                'Right_Knee',
                'Right_Ankle', 
                'Right_Shoulder', 
                'Right_Elbow', 
                #'Right_Wrist',
                'Left_Hip',
                'Left_Knee', 
                'Left_Ankle', 
                'Left_Shoulder',
                'Left_Elbow', 
                #'Left_Wrist', 
            ]

oneD_theta = ['Right_Knee','Right_Elbow','Left_Knee','Left_Elbow']

root = "Waist"

# "RightJoints": [3, 4, 5, 6, 7, 8],
# "LeftJoints": [9, 10, 11, 12, 13, 14],

#time (1), root pos(3), rot orient(4), chest orient(4), neck orient(4), r.hip orient(4), r.knee orient(1), r.ankle(44), r.shoulder orient(4), r.elbow orient(1), l.hip orient(4), l.knee orient (1), l.ankle(4), l.shoulder orient(4), l.elbow orient(1)

json_mimic = {
    "Loop": "wrap",
    "Frames": []
}

for k in keys:
    l_output = []

    l_output.append(0.0625)

    all_theta = np.array(data[str(k)]['theta'])[0]
    joints = np.array(data[str(k)]['joints3d'])
    root_pos = (joints[2] + joints[3]) / 2
    print(root_pos.shape)
    l_output += root_pos.tolist()

    camera = all_theta[:3]
    #Angle de vue a changer ?


    rotation_matrices = tf.Session().run(batch_rodrigues(tf.convert_to_tensor(all_theta[3:72+3].reshape(-1,3),dtype=tf.float32)))
    quater_rot = []
    for k in range(len(rotation_matrices)):
        r = R.from_matrix(rotation_matrices[k]).as_quat()
        quater_rot.append(r)

    l_output += quater_rot[theta_names.index(root)].tolist()

    for k in range(len(theta_wanted)):
        if theta_wanted[k] in oneD_theta:
            oneD_rot = all_theta[3:72+3].reshape(-1,3)[theta_names.index(theta_wanted[k]),-1]
            l_output.append(oneD_rot)
        else :
            l_output += quater_rot[theta_names.index(theta_wanted[k])].tolist()
    
    json_mimic['Frames'].append(l_output)

json.dump(json_mimic,open('deepmimic.txt','w'))


