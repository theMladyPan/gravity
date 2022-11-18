#version 430

// Set up our compute groups
layout(local_size_x=COMPUTE_SIZE_X, local_size_y=COMPUTE_SIZE_Y) in;

float max_f1 = 0.01;
float max_f2 = 0.03;
// Input uniforms go here if you need them.
// Some examples:
//uniform vec2 screen_size;
//uniform vec2 force;
//uniform float frame_time;

// Structure of the ball data
struct Ball
{
    vec4 pos;
    vec4 vel;
    vec4 color;
};

// Input buffer
layout(std430, binding=0) buffer balls_in
{
    Ball balls[];
} In;

// Output buffer
layout(std430, binding=1) buffer balls_out
{
    Ball balls[];
} Out;

void main()
{
    int curBallIndex = int(gl_GlobalInvocationID);

    Ball in_ball = In.balls[curBallIndex];

    vec4 p = in_ball.pos.xyzw;
    vec4 v = in_ball.vel.xyzw;

    vec4 c = in_ball.color.xyzw;
    // Move the ball according to the current force
    p.xyz += v.xyz;
    float weight = pow(p.w, 3);

    float total_force = 0;

    // Calculate the new force based on all the other bodies
    for (int i=0; i < In.balls.length(); i++) {
        // If enabled, this will keep the star from calculating gravity on itself
        // However, it does slow down the calcluations do do this check.
        //  if (i == x)
        //      continue;

        // Calculate distance squared
        float dist = distance(In.balls[i].pos.xyzw.xyz, p.xyz);
        float distanceSquared = dist * dist;

        // If stars get too close the fling into never-never land.
        // So use a minimum distance
        float minDistance = .01;
        float gravityStrength = .1;
        float simulationSpeed = 0.002;

        //calculate gravity
        float gravity = gravityStrength * pow(In.balls[i].pos.xyzw.w, 3) * pow(p.w, 3);

        if(dist > minDistance)
        {
            float force = (gravity / distanceSquared) * -simulationSpeed;
            total_force += force;
            
            vec3 diff = p.xyz - In.balls[i].pos.xyzw.xyz;
            // We should normalize this I think, but it doesn't work.
            //  diff = normalize(diff);
            vec3 delta_v = diff * force;
            v.xyz += delta_v;
            // v.xyz *= 0.99999999;
        }
        else
        {   
            vec3 momentum1 = v.xyz * v.w;
            vec3 momentum2 = In.balls[i].vel.xyz * In.balls[i].vel.w ;
            vec3 momentum = momentum1 + momentum2;
            // we probably hitted sth
            v.xyz = (v.xyz + In.balls[i].vel.xyz)/2.1;
            In.balls[i].vel.xyz = (v.xyz + In.balls[i].vel.xyz)/2.1;
           // break;
        }
    }

    total_force = abs(total_force);

    Ball out_ball;
    out_ball.pos.xyzw = p.xyzw;
    out_ball.vel.xyzw = v.xyzw;
    
    //calculate ball color based on force applied
    c.x = .7 + pow(min(1, total_force/max_f2)*0.3, 2);
    c.y = .3 + pow(min(1, total_force/max_f1)*0.7, 2);
    c.z = pow(min(1.2, total_force/max_f1), 2);
    out_ball.color.xyzw = c.xyzw;

    Out.balls[curBallIndex] = out_ball;
}
